"""11.4 — Activation-memory factor of sequence parallelism at TP = 8.

Usage: python solve.py --out DIR      Evidence label: [MODELED] (assumptions [ILLUSTRATIVE], Table 11.4)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml


def rnd(obj, nd: int = 4):
    """Round floats for deterministic output: 4 significant digits for very large/small, else nd decimals."""
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, float):
        if obj != obj:
            return None
        return float(f"{obj:.{nd}g}") if abs(obj) >= 1e6 or (obj != 0 and abs(obj) < 1e-3) else round(obj, nd)
    if isinstance(obj, dict):
        return {str(k): rnd(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rnd(v, nd) for v in obj]
    return obj


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(rnd(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8")
    print(md)

TP = 8
S, B, H = 4096, 1, 8192           # W-TRAIN (Table 11.4) for the absolute numbers


def solve() -> dict:
    without = 10 + 24 / TP        # bytes per s*b*h per layer, selective recompute, no SP
    with_sp = 34 / TP
    sbh = S * B * H
    return {"inputs": {"tp": TP, "s": S, "b": B, "h": H},
            "answer": {"coeff_without_sp": without, "coeff_with_sp": with_sp, "factor": without / with_sp,
                       "per_layer_mb_without": sbh * without / 1e6, "per_layer_mb_with": sbh * with_sp / 1e6},
            "units": {"coeff": "bytes per (s*b*h) per layer", "per_layer": "MB"}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    # Key 11.4: 13 vs 4.25 -> ~3.1x (tolerance 0.05).
    a = r["answer"]
    assert a["coeff_without_sp"] == 13.0 and a["coeff_with_sp"] == 4.25
    assert abs(a["factor"] - 3.1) < 0.05


def report(r: dict) -> str:
    a = r["answer"]
    return f"""# 11.4 — Sequence parallelism `[MODELED]`

without SP: 10 + 24/8 = {a['coeff_without_sp']} s*b*h; with SP: 34/8 = {a['coeff_with_sp']} s*b*h
factor = {a['factor']:.2f}x; W-TRAIN per layer: {a['per_layer_mb_without']:.0f} MB -> {a['per_layer_mb_with']:.0f} MB
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r))


if __name__ == "__main__":
    main()
