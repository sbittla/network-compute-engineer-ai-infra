"""12.3 — busbw correction factors for five collectives on 16 ranks.

Usage: python solve.py --out DIR      Evidence label: [MODELED]
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np


def rnd(obj, nd: int = 4):
    """Round floats for deterministic output."""
    if isinstance(obj, (bool, np.bool_)) or obj is None:
        return bool(obj) if isinstance(obj, np.bool_) else obj
    if isinstance(obj, (float, np.floating)):
        obj = float(obj)
        return float(f"{obj:.{nd}g}") if abs(obj) >= 1e6 or (obj != 0 and abs(obj) < 1e-3) else round(obj, nd)
    if isinstance(obj, dict):
        return {str(k): rnd(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rnd(v, nd) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


def emit(out: Path, result: dict, md: str, extra: dict | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(rnd(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8")
    for name, text in (extra or {}).items():
        (out / name).write_text(text, encoding="utf-8")
    print(md)

N = 16
OPS = ["all_reduce", "all_gather", "reduce_scatter", "broadcast", "alltoall"]


def factor(op: str, n: int) -> float:
    return {"all_reduce": 2 * (n - 1) / n, "all_gather": (n - 1) / n, "reduce_scatter": (n - 1) / n,
            "alltoall": (n - 1) / n, "broadcast": 1.0}[op]


def solve() -> dict:
    return {"inputs": {"n": N}, "answer": {op: factor(op, N) for op in OPS}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    # Key 12.3: 1.875, 0.9375, 0.9375, 1, 0.9375 (exact).
    assert r["answer"] == {"all_reduce": 1.875, "all_gather": 0.9375, "reduce_scatter": 0.9375,
                           "broadcast": 1.0, "alltoall": 0.9375}


def report(r: dict) -> str:
    rows = "\n".join(f"| {k} | {v} |" for k, v in r["answer"].items())
    return f"# 12.3 — busbw factors, n = 16 `[MODELED]`\n\n| Collective | Factor |\n|---|---|\n{rows}\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r), extras(r) if "extras" in globals() else None)


if __name__ == "__main__":
    main()
