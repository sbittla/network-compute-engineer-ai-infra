"""11.2 — Bytes per parameter for ZeRO-1/2/3 with DP = 8.

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

WEIGHTS_B, GRADS_B = 2, 2          # BF16
OPT_B = 4 + 4 + 4                  # FP32 master, Adam m, Adam v
DP = 8                             # prompt


def solve() -> dict:
    z1 = WEIGHTS_B + GRADS_B + OPT_B / DP
    z2 = WEIGHTS_B + (GRADS_B + OPT_B) / DP
    z3 = (WEIGHTS_B + GRADS_B + OPT_B) / DP
    p_local = 70e9 / (8 * 4)       # W-TRAIN baseline cross-check (TP 8, PP 4)
    return {"inputs": {"weights_b": WEIGHTS_B, "grads_b": GRADS_B, "optimizer_b": OPT_B, "dp": DP},
            "answer": {"total_unsharded_b": WEIGHTS_B + GRADS_B + OPT_B, "zero1_b": z1, "zero2_b": z2, "zero3_b": z3},
            "crosscheck": {"baseline_states_gb_zero1": p_local * z1 / 1e9},
            "units": {"answer": "bytes per local parameter"}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    a = r["answer"]
    # Key 11.2: 16 B, 5.5 B, 3.75 B, 2.0 B (exact); baseline 12.03 GB (tolerance 0.01 GB).
    assert (a["total_unsharded_b"], a["zero1_b"], a["zero2_b"], a["zero3_b"]) == (16, 5.5, 3.75, 2.0)
    assert abs(r["crosscheck"]["baseline_states_gb_zero1"] - 12.03) < 0.01


def report(r: dict) -> str:
    a = r["answer"]
    return f"""# 11.2 — Bytes per parameter `[MODELED]`

16 B = 2 (BF16 weights) + 2 (BF16 grads) + 12 (FP32 master + Adam m + v).

| Stage (DP = 8) | Formula | Bytes/param |
|---|---|---|
| ZeRO-1 | 2 + 2 + 12/8 | {a['zero1_b']} |
| ZeRO-2 | 2 + (2 + 12)/8 | {a['zero2_b']} |
| ZeRO-3 | 16/8 | {a['zero3_b']} |

Cross-check: W-TRAIN baseline ZeRO-1 states = 2.1875e9 x 5.5 B = {r['crosscheck']['baseline_states_gb_zero1']:.2f} GB.
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
