"""Exercise 6.8: intensity of a BF16 linear layer (K = N = 4,096) vs tokens M, and the compute-bound threshold.

Usage: python solve.py --out DIR
Model (Section 6.2): W = 2MKN FLOP; minimum Q = 2(MK + KN + MN) B (each operand read once, output written
once, BF16); I = W / Q; time at roof = max(W / P, Q / B). Ceilings: 989 TFLOP/s, 3.35 TB/s (Table 6.1).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

K = N = 4_096
P = 989e12
BW = 3.35e12
KEY = {4096: {"I": 1365, "t_us": 139, "bound": "compute"}, 64: {"I": 62.1, "t_us": 10.3, "bound": "memory"}}
KEY_M_STAR = 345   # exercises-key.md 6.8 (c)


def sci(x: float) -> str:
    """Format as 'm.mmm × 10^e' with superscript exponent (house style)."""
    e = int(f"{x:e}".split("e")[1])
    sup = str(e).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
    return f"{x / 10**e:.3f} × 10{sup}"


def layer(m: int) -> dict:
    w = 2 * m * K * N
    q = 2 * (m * K + K * N + m * N)
    i = w / q
    bound = "compute" if i >= P / BW else "memory"
    t = max(w / P, q / BW)
    attain = min(P, i * BW)
    return {"M": m, "W_flop": w, "Q_bytes": q, "I_flop_per_B": round(i, 2), "bound": bound,
            "t_roof_us": round(t * 1e6, 2), "attainable_TFLOPs": round(attain / 1e12, 1),
            "fraction_of_peak": round(attain / P, 3)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    ridge = P / BW
    cases = {m: layer(m) for m in (4096, 64)}
    for m, k in KEY.items():
        c = cases[m]
        assert abs(c["I_flop_per_B"] - k["I"]) / k["I"] < 0.005 and c["bound"] == k["bound"], c
        assert abs(c["t_roof_us"] - k["t_us"]) / k["t_us"] < 0.01, c
    # (c) solve 2MKN / (2(MK + KN + MN)) = ridge with K = N: I(M) = K M / (2M + K)  ->  M* = ridge K / (K - 2 ridge)
    m_star = ridge * K / (K - 2 * ridge)
    m_int = next(m for m in range(1, 10_000) if layer(m)["I_flop_per_B"] >= ridge)
    assert abs(m_star - KEY_M_STAR) < 1 and m_int == 345, (m_star, m_int)
    res = {"exercise": "6.8", "evidence_label": "MODELED",
           "inputs": {"K": K, "N": N, "peak_flops": P, "hbm_Bps": BW, "dtype_bytes": 2},
           "steps": {"ridge_flop_per_B": round(ridge, 2)},
           "answer": {"a_M4096": cases[4096], "b_M64": cases[64], "c_M_star_exact": round(m_star, 2),
                      "c_smallest_integer_M": m_int},
           "units": {"W": "FLOP", "Q": "B", "I": "FLOP/B", "t": "µs"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 6.8 — intensity and batch size `[MODELED]`", "", f"Ridge = 989 / 3.35 = {ridge:.1f} FLOP/B.", "",
          "| M | W (FLOP) | Q (B) | I (FLOP/B) | Bound | Time at roof | Attainable |", "|---|---|---|---|---|---|---|"]
    for c in cases.values():
        md.append(f"| {c['M']:,} | {sci(c['W_flop'])} | {c['Q_bytes']:,} | {c['I_flop_per_B']:,.1f} | {c['bound']} | "
                  f"{c['t_roof_us']:.1f} µs | {c['attainable_TFLOPs']:.0f} TFLOP/s ({c['fraction_of_peak'] * 100:.0f} %) |")
    md += ["", f"(c) I(M) = 4,096 M / (2M + 4,096) = {ridge:.1f} → M = {ridge:.1f} × 4,096 / (4,096 − 2 × {ridge:.1f}) = "
           f"{m_star:.1f} → smallest compute-bound M = {m_int} tokens."]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
