"""Exercise 6.15: GPU-hour budget of the nightly regression gate (model answer's schedule).

Usage: python solve.py --out DIR
Inputs: budget 16 GPU-hours per night (prompt); two dedicated HX8 nodes (8 GPUs each) reserved for the
whole window, so reserved GPU-time is what counts; schedule from the model answer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

BUDGET_GPU_H = 16.0
NODES, GPUS_PER_NODE = 2, 8
STAGES = [  # name, minutes (both nodes in parallel), runs
    ("microbenchmark suite (GEMM BF16/FP8 × 3 shapes, LayerNorm, attention)", 20, None),
    ("single-node all_reduce_perf, 8 GPUs", 10, None),
    ("end-to-end W-TRAIN proxy, TP = 8, 12 × 2-minute runs per node (rotating node: 6 candidate + 6 baseline "
     "interleaved; reference node: 6 + 6 baseline A/A), plus 6 min setup", 30, 12),
]
E2E_RUN_MIN, E2E_SETUP_MIN, RUNS_PER_ARM = 2, 6, 6
KEY_GPU_H = 16.0   # exercises-key.md 6.15: "two dedicated nodes x 8 GPUs x 1 h"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    minutes = sum(m for _, m, _ in STAGES)
    gpus = NODES * GPUS_PER_NODE
    gpu_h = gpus * minutes / 60
    e2e_runs_per_node = 2 * RUNS_PER_ARM          # two arms (A/B on the rotating node, A/A on the reference node)
    e2e_run_min = e2e_runs_per_node * E2E_RUN_MIN
    assert gpu_h <= BUDGET_GPU_H and abs(gpu_h - KEY_GPU_H) < 1e-9, gpu_h
    assert e2e_runs_per_node == STAGES[2][2]
    assert e2e_run_min + E2E_SETUP_MIN <= STAGES[2][1]   # 12 × 2 min + 6 min setup fits the 30-minute slot
    rows = [{"stage": n, "minutes": m, "gpu_hours": round(gpus * m / 60, 2)} for n, m, _ in STAGES]
    res = {"exercise": "6.15", "evidence_label": "MODELED",
           "inputs": {"budget_gpu_h": BUDGET_GPU_H, "nodes": NODES, "gpus_per_node": GPUS_PER_NODE},
           "answer": {"stages": rows, "window_minutes": minutes, "gpu_hours": gpu_h,
                      "headroom_gpu_h": BUDGET_GPU_H - gpu_h, "e2e_measured_minutes": e2e_run_min,
                      "e2e_runs_per_node": e2e_runs_per_node, "runs_per_arm": RUNS_PER_ARM},
           "units": {"time": "minutes", "budget": "GPU-hours"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 6.15 — nightly gate budget `[MODELED]`", "",
          "| Stage | Minutes | GPU-hours (16 GPUs reserved) |", "|---|---|---|"]
    md += [f"| {r['stage']} | {r['minutes']} | {r['gpu_hours']:.2f} |" for r in rows]
    md += [f"| Total | {minutes} | {gpu_h:.1f} of {BUDGET_GPU_H:.0f} |"]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
