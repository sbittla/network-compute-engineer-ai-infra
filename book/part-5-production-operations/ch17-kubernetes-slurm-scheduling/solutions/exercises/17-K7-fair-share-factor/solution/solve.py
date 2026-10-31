"""17-K7 — Classic Slurm fair-share factor F = 2^(-U/S).

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


CASES = {"usage = share": 1.0, "usage = half share": 0.5, "usage = twice share": 2.0}
KEY = {"usage = share": 0.5, "usage = half share": 0.707, "usage = twice share": 0.25}
W_FAIRSHARE = 10000   # ORION PriorityWeightFairshare (Section 17.5.4)


def main(out: Path) -> None:
    f = {k: 2 ** (-u) for k, u in CASES.items()}
    for k in CASES:
        close(f[k], KEY[k], 0.0005, k)
    gap = W_FAIRSHARE * (f["usage = half share"] - f["usage = twice share"])
    result = {"exercise": "17-K7", "evidence_label": "[MODELED]", "inputs": {"U_over_S": CASES},
              "answer": {k: round(v, 4) for k, v in f.items()},
              "steps": {"priority_points_gap_half_vs_twice": round(gap, 1)}, "units": {"F": "dimensionless"}}
    md = "# 17-K7 result `[MODELED]`\n\n" + "\n".join(f"- {k}: F = 2^(-{u:g}) = {f[k]:.3f}" for k, u in CASES.items())
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
