"""11.3 — 1F1B bubble fraction (p - 1)/(m + p - 1).

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

CASES = [(4, 8), (4, 32), (4, 128), (8, 32)]       # (p, m) from the prompt
KEY = {(4, 8): 0.273, (4, 32): 0.086, (4, 128): 0.023, (8, 32): 0.179}


def solve() -> dict:
    rows = []
    for p, m in CASES:
        rows.append({"p": p, "m": m, "of_total": (p - 1) / (m + p - 1), "of_ideal": (p - 1) / m,
                     "fraction": f"{p - 1}/{m + p - 1}"})
    return {"inputs": {"cases": CASES}, "answer": rows, "units": {"bubble": "fraction of total pipeline time"},
            "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    for row in r["answer"]:
        # Key 11.3 values to 3 decimals; tolerance 0.0005.
        assert abs(row["of_total"] - KEY[(row["p"], row["m"])]) < 0.0005, row


def report(r: dict) -> str:
    lines = ["# 11.3 — 1F1B bubble `[MODELED]`", "", "| p | m | (p-1)/(m+p-1) | of total | (p-1)/m |", "|---|---|---|---|---|"]
    for row in r["answer"]:
        lines.append(f"| {row['p']} | {row['m']} | {row['fraction']} | {row['of_total'] * 100:.1f} % | {row['of_ideal'] * 100:.1f} % |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r))


if __name__ == "__main__":
    main()
