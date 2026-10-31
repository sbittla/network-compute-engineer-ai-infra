#!/usr/bin/env python3
"""W2 — Young's checkpoint interval, waste and run duration with M = 24 h [MODELED].

Usage: python solve.py --out DIR   (writes result.json and result.md; asserts the answer key)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def r(x: float, nd: int = 4) -> float:
    return round(float(x), nd)


def write(out: Path, result: dict, md_lines: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    (out / "result.md").write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")


def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol

# Inputs: exercises.md W2 [ILLUSTRATIVE]; canonical R from REFERENCE_CLUSTER / Section 23.10.
DELTA_S = 60.0           # blocking checkpoint cost
R_S = 900.0              # restart cost
M_S = 24 * 3600.0        # variation: node MTBF 768 h / 32 nodes
GPUS = 256
OTHER_LOSS = 0.05        # scheduling gaps, maintenance, stragglers
IDEAL_DAYS = 96.00
DELTA_ASYNC_S = 5.0      # backlog option: asynchronous checkpoint


def waste(delta: float, m: float, rr: float) -> tuple[float, float, float, float]:
    tau = math.sqrt(2 * delta * m)
    a, b, c = delta / tau, tau / (2 * m), rr / m
    return tau, a, b, c


def main(out: Path) -> None:
    tau, a, b, c = waste(DELTA_S, M_S, R_S)
    total = a + b + c
    lost_s = tau / 2 + R_S
    lost_gpu_h = lost_s * GPUS / 3600
    goodput = 1 - total - OTHER_LOSS
    days = IDEAL_DAYS / goodput
    tau5, a5, b5, c5 = waste(DELTA_ASYNC_S, M_S, R_S)
    total5 = a5 + b5 + c5
    days5 = IDEAL_DAYS / (1 - total5 - OTHER_LOSS)
    tau48, a48, b48, c48 = waste(DELTA_S, 48 * 3600.0, R_S)

    assert close(tau, 3219.9, 0.1)                                  # key: 3,219.9 s
    assert close(100 * a, 1.863, 0.001) and close(100 * b, 1.863, 0.001) and close(100 * c, 1.042, 0.001)
    assert close(100 * total, 4.77, 0.005)
    assert close(lost_gpu_h, 178.5, 0.05)
    assert close(goodput, 0.9023, 0.0001) and close(days, 106.39, 0.005)
    assert close(tau5, 929.5, 0.1) and close(100 * total5, 2.12, 0.005) and close(days5, 103.36, 0.01)
    assert close(100 * (total - total5), 2.65, 0.01) and close(days - days5, 3.0, 0.05)
    assert close(100 * (a48 + b48 + c48), 3.16, 0.005)              # canonical, Section 23.10

    result = {
        "id": "W2", "evidence_label": "MODELED",
        "inputs": {"delta_s": DELTA_S, "R_s": R_S, "M_s": M_S, "gpus": GPUS, "other_loss": OTHER_LOSS,
                   "ideal_days": IDEAL_DAYS},
        "steps": {"tau_s": r(tau, 1), "ckpt_overhead_pct": r(100 * a, 3), "rework_pct": r(100 * b, 3),
                  "restart_pct": r(100 * c, 3), "lost_s_per_failure": r(lost_s, 1)},
        "answer": {"total_waste_pct": r(100 * total, 2), "lost_gpu_hours_per_failure": r(lost_gpu_h, 1),
                   "goodput": r(goodput, 4), "duration_days": r(days, 2),
                   "backlog_first": "reduce delta (validate asynchronous checkpoint)",
                   "async": {"tau_s": r(tau5, 1), "total_waste_pct": r(100 * total5, 2),
                             "duration_days": r(days5, 2), "days_saved": r(days - days5, 2)},
                   "canonical_M48_total_waste_pct": r(100 * (a48 + b48 + c48), 2)},
        "units": {"tau_s": "s", "pct": "%", "duration": "days", "lost": "GPU-hours"},
    }
    md = [
        "# W2 — checkpoint interval and goodput `[MODELED]`", "",
        f"1. τ = sqrt(2 × {DELTA_S:.0f} × {M_S:,.0f}) = {tau:,.1f} s; δ/τ = {100 * a:.3f} %; τ/(2M) = {100 * b:.3f} %; "
        f"R/M = {100 * c:.3f} %; total {100 * total:.2f} %",
        f"2. ({tau / 2:,.1f} + {R_S:.0f}) s × {GPUS} / 3,600 = {lost_gpu_h:.1f} GPU-hours per failure",
        f"3. goodput = 1 − {total:.4f} − {OTHER_LOSS} = {goodput:.4f}; {IDEAL_DAYS:.2f} / {goodput:.4f} = {days:.2f} days",
        f"4. async δ = {DELTA_ASYNC_S:.0f} s: τ = {tau5:.1f} s, waste {100 * total5:.2f} %, {days5:.2f} days "
        f"({days - days5:.2f} days shorter); canonical M = 48 h waste {100 * (a48 + b48 + c48):.2f} %",
    ]
    write(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    main(ap.parse_args().out)
