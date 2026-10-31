"""17-W1 — Gang feasibility, best fit, deadlock and preemption cost (Chapter 17).

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


FREE = dict(zip([f"p{i:02d}" for i in range(1, 13)], [8, 8, 0, 4, 6, 2, 8, 3, 5, 8, 1, 7]))
DRAINING = {"p07"}
GPUS_PER_NODE = 8
PRICE = 2.50                 # $/GPU-hour [ILLUSTRATIVE]
STRAND_H = 5.0
JOB_GPUS, CKPT_MIN, RESTART_MIN = 128, 45.0, 15.0


def main(out: Path) -> None:
    naive = sum(FREE.values())
    eligible = {n: f for n, f in FREE.items() if n not in DRAINING}
    eligible_free = sum(eligible.values())
    whole = sorted(n for n, f in eligible.items() if f == GPUS_PER_NODE)
    largest_gang = len(whole) * GPUS_PER_NODE
    need = 4
    reason = ("placed" if len(whole) >= need else
              "Fragmentation" if eligible_free >= need * GPUS_PER_NODE else "InsufficientCapacity")
    cands = sorted((f - 6, n) for n, f in eligible.items() if f >= 6)
    best = cands[0][1]
    stranded = 4 * GPUS_PER_NODE          # 2 + 2 nodes held by two half-placed 3-node jobs
    strand_gpu_h = stranded * STRAND_H
    cost = strand_gpu_h * PRICE
    lost = JOB_GPUS * (CKPT_MIN / 2 + RESTART_MIN) / 60

    assert naive == 60 and eligible_free == 52
    assert whole == ["p01", "p02", "p10"] and largest_gang == 24
    assert reason == "Fragmentation"
    assert best == "p05"
    assert stranded == 32 and strand_gpu_h == 160 and cost == 400
    close(lost, 80, 1e-9, "GPU-hours lost per preemption")

    result = {"exercise": "17-W1", "evidence_label": "[MODELED]",
              "inputs": {"free": FREE, "draining": sorted(DRAINING), "price_per_gpu_h": PRICE,
                         "checkpoint_min": CKPT_MIN, "restart_min": RESTART_MIN, "job_gpus": JOB_GPUS},
              "answer": {"1_naive": naive, "1_eligible": eligible_free, "2_whole_nodes": whole,
                         "2_largest_gang_gpus": largest_gang, "3_reason": reason,
                         "4_best_fit": best, "4_leftovers": {n: l for l, n in cands},
                         "5_stranded_gpus": stranded, "5_gpu_hours": strand_gpu_h, "5_cost_usd": cost,
                         "6_gpu_hours_per_preemption": round(lost, 2)},
              "units": {"gpus": "GPUs", "cost": "USD [ILLUSTRATIVE]", "loss": "GPU-hours"}}
    md = f"""
# 17-W1 result `[MODELED]`

1. naive {naive} GPUs; eligible {eligible_free} (draining p07 excluded)
2. whole eligible nodes {whole} → largest gang {largest_gang} GPUs
3. 4-node gang: {reason}
4. best fit for 6 GPUs: {best} (leftovers {[(n, l) for l, n in cands]})
5. {stranded} GPUs stranded × {STRAND_H:g} h = {strand_gpu_h:g} GPU-hours = ${cost:,.0f}
6. {JOB_GPUS} × ({CKPT_MIN:g}/2 + {RESTART_MIN:g}) min = {lost:g} GPU-hours per preemption
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
