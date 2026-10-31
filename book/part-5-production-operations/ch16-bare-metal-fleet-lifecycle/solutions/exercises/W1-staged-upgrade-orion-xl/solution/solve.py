"""W1 — Staged upgrade for ORION-XL (Chapter 16, Section 16.8).

Usage: python solve.py --out DIR
Writes result.json and result.md; asserts the answer key (solutions/exercises-key.md).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8", newline="\n")


def close(value: float, key: float, tol: float, what: str) -> None:
    assert abs(value - key) <= tol, f"{what}: computed {value} vs key {key} (tol {tol})"


# Prompt parameters (exercises.md, W1)
NODES, RACKS, NODES_PER_RACK = 512, 128, 4
CANARY_NODES, CANARY_BAKE_H = 4, 72.0
WAVE_CAP, RACK_CAP = 32, 1
WAVE_H, BAKE_H = 3.0, 6.0
GPUS_PER_NODE = 8
LAMBDAS = {"1 per 100 node-hours": 1 / 100, "1 per 1,000 node-hours": 1 / 1000}


def main(out: Path) -> None:
    remaining = NODES - CANARY_NODES
    largest_rack_remainder = NODES_PER_RACK          # racks that held no canary node
    waves = max(math.ceil(remaining / WAVE_CAP), math.ceil(largest_rack_remainder / RACK_CAP))
    assert WAVE_CAP <= RACKS, "a full wave needs one rack per node"
    sizes = [WAVE_CAP] * (remaining // WAVE_CAP) + ([remaining % WAVE_CAP] if remaining % WAVE_CAP else [])
    calendar_h = (WAVE_H + CANARY_BAKE_H) + waves * (WAVE_H + BAKE_H)
    node_hours = NODES * WAVE_H
    gpu_hours = node_hours * GPUS_PER_NODE
    nt = CANARY_NODES * CANARY_BAKE_H
    detect = {k: 1 - math.exp(-lam * nt) for k, lam in LAMBDAS.items()}
    nt_90 = math.log(10) / (1 / 1000)

    assert waves == 16 and sizes.count(32) == 15 and sizes[-1] == 28
    close(calendar_h, 219.0, 1e-9, "calendar hours")
    close(node_hours, 1536, 0, "node-hours")
    close(gpu_hours, 12288, 0, "GPU-hours")
    close(detect["1 per 100 node-hours"], 0.944, 0.0005, "P(detect) lambda=0.01")
    close(detect["1 per 1,000 node-hours"], 0.250, 0.0005, "P(detect) lambda=0.001")
    close(nt_90, 2303, 0.5, "node-hours for 90 %")

    result = {
        "exercise": "W1", "evidence_label": "[MODELED]",
        "inputs": {"nodes": NODES, "racks": RACKS, "canary_nodes": CANARY_NODES, "canary_bake_h": CANARY_BAKE_H,
                   "wave_cap": WAVE_CAP, "per_rack_cap": RACK_CAP, "wave_h": WAVE_H, "bake_h": BAKE_H},
        "steps": {"remaining_after_canary": remaining, "waves_by_cap": math.ceil(remaining / WAVE_CAP),
                  "waves_by_rack": largest_rack_remainder, "wave_sizes": sizes,
                  "canary_node_hours": nt},
        "answer": {"a_waves": waves, "b_calendar_h": round(calendar_h, 1), "b_calendar_days": round(calendar_h / 24, 2),
                   "c_node_hours": node_hours, "c_gpu_hours": gpu_hours,
                   "d_p_detect": {k: round(v, 4) for k, v in detect.items()},
                   "e_node_hours_for_90pct": round(nt_90, 1)},
        "units": {"calendar": "h", "capacity": "node-hours / GPU-hours", "probability": "fraction"},
    }
    md = f"""
# W1 result `[MODELED]`

| Part | Formula | Result |
|---|---|---|
| (a) | max(ceil({remaining}/{WAVE_CAP}), {largest_rack_remainder}/{RACK_CAP}) | {waves} waves ({sizes.count(32)} × 32 + 1 × {sizes[-1]}) |
| (b) | ({WAVE_H:g} + {CANARY_BAKE_H:g}) + {waves} × ({WAVE_H:g} + {BAKE_H:g}) | {calendar_h:.0f} h = {calendar_h / 24:.1f} days |
| (c) | {NODES} × {WAVE_H:g} h; × {GPUS_PER_NODE} | {node_hours:,.0f} node-hours = {gpu_hours:,.0f} GPU-hours |
| (d) | 1 − exp(−0.01 × {nt:g}) | {detect['1 per 100 node-hours'] * 100:.1f} % |
| (d) | 1 − exp(−0.001 × {nt:g}) | {detect['1 per 1,000 node-hours'] * 100:.1f} % |
| (e) | ln 10 / 0.001 | {nt_90:,.0f} node-hours |
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
