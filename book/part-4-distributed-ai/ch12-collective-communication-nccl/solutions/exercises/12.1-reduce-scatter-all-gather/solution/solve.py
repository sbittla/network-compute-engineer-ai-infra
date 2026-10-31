"""12.1 — Two-rank reduce-scatter and all-gather, composed and compared with all-reduce.

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

R = np.array([[1, 2], [10, 20]])       # R0, R1 (example chosen in the answer)


def solve() -> dict:
    n = R.shape[0]
    total = R.sum(axis=0)
    rs = [total[r:r + 1].tolist() for r in range(n)]                # rank r keeps chunk r
    ag = [sum(rs, []) for _ in range(n)]                             # everyone gets all chunks
    ar = [total.tolist() for _ in range(n)]
    return {"inputs": {"ranks": R.tolist()}, "reduce_scatter": rs, "all_gather_of_rs": ag, "all_reduce": ar,
            "answer": {"composition_equals_all_reduce": ag == ar}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    # Key 12.1: reduce-scatter R0 [11], R1 [22]; all-gather -> [11, 22] = all-reduce.
    assert r["reduce_scatter"] == [[11], [22]] and r["all_gather_of_rs"] == [[11, 22], [11, 22]]
    assert r["answer"]["composition_equals_all_reduce"]


def report(r: dict) -> str:
    return f"""# 12.1 — Composition `[MODELED]`

inputs {r['inputs']['ranks']}; reduce-scatter {r['reduce_scatter']}; all-gather {r['all_gather_of_rs']};
all-reduce {r['all_reduce']}; equal: {r['answer']['composition_equals_all_reduce']}
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r), extras(r) if "extras" in globals() else None)


if __name__ == "__main__":
    main()
