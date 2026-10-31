#!/usr/bin/env python3
"""D1 — canary GPU cost and detectable effect for continuous regression detection.

Usage: python solve.py --out DIR   (writes result.json and result.md; asserts the answer key)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def r(x: float, nd: int = 4) -> float:
    return round(float(x), nd)


def write(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    (out / "result.md").write_text(md.rstrip() + "\n", encoding="utf-8")


CLUSTER_GPUS = 256                    # ORION-256 (docs/REFERENCE_CLUSTER.md)
HOURS_PER_DAY = 24
CANARY_GPUS, CANARY_HOURS = 64, 1.0   # one 64-GPU W-TRAIN ablation per day
STEP_S = 17.4                         # W-TRAIN modeled step at 40 % MFU
REGRESSION = 0.03                     # target: detect >= 3 %
SIGMA_S = 0.11                        # run-to-run sigma of per-job means (lab before period)
Z_SUM = 2.8                           # 1.96 + 0.84
BASELINE_N = 7                        # rolling 7-day baseline
KEY = {"canary_pct": 1.04, "n_needed": 0.70, "delta_s": 0.52}   # exercises-key.md D1


def main(out: Path) -> None:
    canary_pct = 100 * CANARY_GPUS * CANARY_HOURS / (CLUSTER_GPUS * HOURS_PER_DAY)
    delta = REGRESSION * STEP_S
    n_needed = 2 * (Z_SUM * SIGMA_S / delta) ** 2
    mde7 = Z_SUM * SIGMA_S * math.sqrt(2 / BASELINE_N)
    threshold = STEP_S + max(3 * SIGMA_S, REGRESSION * STEP_S)
    assert abs(canary_pct - KEY["canary_pct"]) <= 0.005
    assert abs(n_needed - KEY["n_needed"]) <= 0.005
    assert abs(delta - KEY["delta_s"]) <= 0.005
    assert mde7 < delta, "the 7-day baseline must resolve a 3 % regression"
    result = {"id": "D1", "evidence_label": "MODELED", "units": "%; runs; s",
              "inputs": {"cluster_gpus": CLUSTER_GPUS, "canary_gpus": CANARY_GPUS, "canary_hours": CANARY_HOURS,
                         "step_s": STEP_S, "regression": REGRESSION, "sigma_s": SIGMA_S, "baseline_n": BASELINE_N},
              "steps": {"canary_gpu_h_per_day": CANARY_GPUS * CANARY_HOURS,
                        "cluster_gpu_h_per_day": CLUSTER_GPUS * HOURS_PER_DAY, "delta_s": r(delta, 3)},
              "answer": {"canary_cost_pct": r(canary_pct, 2), "runs_per_arm_needed": r(n_needed, 2),
                         "mde_7day_baseline_s": r(mde7, 3), "alert_threshold_s": r(threshold, 2)}}
    md = ["# D1 — canary cost and detectability `[MODELED]`", "",
          f"Canary cost: {CANARY_GPUS * CANARY_HOURS:.0f} GPU-h / {CLUSTER_GPUS * HOURS_PER_DAY:,} GPU-h = {canary_pct:.2f} %.",
          f"3 % of {STEP_S} s = {delta:.3f} s; n = 2 × (2.8 × {SIGMA_S} / {delta:.3f})² = {n_needed:.2f} runs per arm.",
          f"7-day baseline MDE = {mde7:.3f} s; alert threshold = {threshold:.2f} s."]
    write(out, result, "\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
