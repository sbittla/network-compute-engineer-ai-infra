"""W2 — Cost of an undetected 9 % regression and a large-job threshold (Chapter 18).

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


GPUS, BASE_S, SLOW_S, PRICE = 4096, 17.4, 19.0, 3.0
CASE_H = {"A": 6.0 + 0.5, "B": (12 + 30) / 60}
THRESHOLD, PROPOSED = 1.10, 1.05
NOISE_SD, MEDIAN_EFF, WINDOW_S = 0.012, 1.25, 600


def main(out: Path) -> None:
    ratio = BASE_S / SLOW_S
    lost = 1 - ratio
    gpu_h = {k: h * GPUS * lost for k, h in CASE_H.items()}
    cost = {k: v * PRICE for k, v in gpu_h.items()}
    step_ratio = SLOW_S / BASE_S
    n = int(WINDOW_S / BASE_S)
    median_sd = MEDIAN_EFF * NOISE_SD / math.sqrt(n)
    sigmas = (PROPOSED - 1) / median_sd
    close(ratio, 0.916, 0.0005, "throughput ratio")
    close(lost, 0.084, 0.0005, "lost fraction")
    close(gpu_h["A"], 2242, 1.0, "case A GPU-h")
    close(cost["A"], 6730, 10, "case A cost")
    close(gpu_h["B"], 241, 0.5, "case B GPU-h")
    close(cost["B"], 724, 1.0, "case B cost")
    assert step_ratio < THRESHOLD and step_ratio > PROPOSED
    assert n == 34
    close(median_sd * 100, 0.26, 0.005, "median sd %")
    close(sigmas, 19, 0.5, "sigmas at 5 %")
    result = {"exercise": "W2", "evidence_label": "[MODELED]",
              "inputs": {"gpus": GPUS, "base_s": BASE_S, "slow_s": SLOW_S, "price_usd_per_gpu_h": PRICE,
                         "case_hours": CASE_H, "noise_sd": NOISE_SD},
              "answer": {"a_ratio": round(ratio, 4), "a_lost": round(lost, 4),
                         "b_gpu_hours": {k: round(v, 1) for k, v in gpu_h.items()},
                         "b_cost_usd": {k: round(v) for k, v in cost.items()},
                         "c_step_ratio": round(step_ratio, 4), "c_fires_at_1_10": step_ratio > THRESHOLD,
                         "c_proposed_threshold": PROPOSED, "c_steps_in_window": n,
                         "c_median_sd_pct": round(median_sd * 100, 3), "c_sigmas": round(sigmas, 1)},
              "units": {"cost": "USD [ILLUSTRATIVE]", "loss": "GPU-hours"}}
    md = f"""
# W2 result `[MODELED]`

- (a) ratio {ratio:.3f}, lost {lost:.3f}
- (b) A: {gpu_h['A']:,.0f} GPU-h = ${cost['A']:,.0f}; B: {gpu_h['B']:,.0f} GPU-h = ${cost['B']:,.0f}
- (c) step ratio {step_ratio:.3f} < {THRESHOLD} → no page; at {PROPOSED}: median sd {median_sd * 100:.2f} % over {n} steps → {sigmas:.0f} sd
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
