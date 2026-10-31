"""K8 — Series count of a per-rank step-time gauge with a step label (Chapter 18).

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


RANKS, STEP_S, DAY_S = 4096, 17.4, 86400


def main(out: Path) -> None:
    steps = math.ceil(DAY_S / STEP_S)
    series = RANKS * steps
    assert steps == 4966
    close(series / 1e6, 20.3, 0.05, "million series per day")
    result = {"exercise": "K8", "evidence_label": "[MODELED]",
              "inputs": {"ranks": RANKS, "step_s": STEP_S, "day_s": DAY_S},
              "answer": {"steps_per_day": steps, "series_per_day": series, "million_series": round(series / 1e6, 2)},
              "units": {"series": "time series per day"}}
    md = f"# K8 result `[MODELED]`\n\n- steps/day = ceil({DAY_S} / {STEP_S}) = {steps:,}\n- series = {RANKS:,} × {steps:,} = {series:,} ≈ {series / 1e6:.1f} million"
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
