"""12.9 — Alpha-beta times, n_half and bucketing cost for a 64-rank all-reduce.

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

N, ALPHA_US, B_GBPS = 64, 47.0, 346.0
SIZES_MB = [4, 25, 256]
TOTAL_B, BUCKET_B = 4.375e9, 25e6


def t_us(size_b: float) -> float:
    f = 2 * (N - 1) / N
    return ALPHA_US + f * size_b / (B_GBPS * 1e9) * 1e6


def solve() -> dict:
    f = 2 * (N - 1) / N
    times = {f"{m}MB": t_us(m * 1e6) for m in SIZES_MB}
    n_half = ALPHA_US * 1e-6 * B_GBPS * 1e9 / f
    n_buckets = round(TOTAL_B / BUCKET_B)
    bucketed_ms = n_buckets * t_us(BUCKET_B) / 1e3
    single_ms = t_us(TOTAL_B) / 1e3
    return {"inputs": {"n": N, "alpha_us": ALPHA_US, "busbw_GBps": B_GBPS, "factor": f},
            "a_times_us": times, "b_n_half_MB": n_half / 1e6,
            "c": {"buckets": n_buckets, "bucketed_ms": bucketed_ms, "single_ms": single_ms,
                  "difference_ms": bucketed_ms - single_ms, "extra_alpha_ms": (n_buckets - 1) * ALPHA_US / 1e3},
            "units": {"time": "us / ms", "n_half": "MB (1e6 B)"}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    t = r["a_times_us"]
    # Key 12.9 (tolerance 0.1 us / 0.01 MB / 0.1 ms).
    assert abs(t["4MB"] - 69.8) < 0.1 and abs(t["25MB"] - 189.3) < 0.1 and abs(t["256MB"] - 1503.6) < 0.1
    assert abs(r["b_n_half_MB"] - 8.26) < 0.01
    c = r["c"]
    assert c["buckets"] == 175 and abs(c["bucketed_ms"] - 33.1) < 0.1 and abs(c["single_ms"] - 24.9) < 0.1
    assert abs(c["difference_ms"] - c["extra_alpha_ms"]) < 0.01


def report(r: dict) -> str:
    t, c = r["a_times_us"], r["c"]
    return f"""# 12.9 — Alpha-beta `[MODELED]`

t(4 MB) = {t['4MB']:.1f} us; t(25 MB) = {t['25MB']:.1f} us; t(256 MB) = {t['256MB']:.1f} us
n_half = {r['b_n_half_MB']:.2f} MB
{c['buckets']} buckets: {c['bucketed_ms']:.1f} ms; one message: {c['single_ms']:.1f} ms; difference {c['difference_ms']:.2f} ms = {c['buckets'] - 1} x 47 us
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
