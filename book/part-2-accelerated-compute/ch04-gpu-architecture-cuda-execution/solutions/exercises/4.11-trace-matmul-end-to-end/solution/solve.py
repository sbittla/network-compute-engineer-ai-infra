"""Exercise 4.11: stage times for a BF16 8,192^3 GEMM whose operands start (and result ends) in host memory.

Usage: python solve.py --out DIR
Inputs (prompt): N = 8,192, BF16 (2 B), 52 GB/s PCIe per direction (pinned), 70 % of 989 TFLOP/s.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

N = 8_192
ELEM_B = 2
PCIE_BPS = 52e9
PEAK_FLOPS = 989e12
EFF = 0.70
KEY_MS = {"h2d": 5.16, "kernel": 1.59, "d2h": 2.58, "total": 9.33}  # exercises-key.md 4.11
KEY_INTENSITY = 2_730      # FLOP/B moved over PCIe
KEY_PCIE_RIDGE = 19_000    # FLOP/B
TOL = 0.01                 # relative


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    mat_b = N * N * ELEM_B
    flop = 2 * N**3
    h2d = 2 * mat_b / PCIE_BPS * 1e3
    kern = flop / (EFF * PEAK_FLOPS) * 1e3
    d2h = mat_b / PCIE_BPS * 1e3
    total = h2d + kern + d2h
    intensity = flop / (3 * mat_b)
    ridge = PEAK_FLOPS / PCIE_BPS
    got = {"h2d": h2d, "kernel": kern, "d2h": d2h, "total": total}
    for k, v in got.items():
        assert abs(v - KEY_MS[k]) <= TOL * KEY_MS[k], (k, v)
    assert abs(intensity - KEY_INTENSITY) <= TOL * KEY_INTENSITY, intensity
    assert abs(ridge - KEY_PCIE_RIDGE) <= 0.01 * KEY_PCIE_RIDGE, ridge
    res = {"exercise": "4.11", "evidence_label": "MODELED",
           "inputs": {"N": N, "element_bytes": ELEM_B, "pcie_Bps": PCIE_BPS, "peak_flops": PEAK_FLOPS, "efficiency": EFF},
           "steps": {"matrix_bytes": mat_b, "flop": flop, "intensity_over_pcie_flop_per_B": round(intensity, 1),
                     "pcie_ridge_flop_per_B": round(ridge)},
           "answer": {"h2d_ms": round(h2d, 3), "kernel_ms": round(kern, 3), "d2h_ms": round(d2h, 3),
                      "total_ms": round(total, 2), "kernel_share": round(kern / total, 3)},
           "units": {"time": "ms", "bytes": "B"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Exercise 4.11 — stage times `[MODELED]`

| Stage | Formula | Time |
|---|---|---|
| H2D (A and B) | 2 × {mat_b:,} B / 52 × 10⁹ B/s | {h2d:.2f} ms |
| Kernel | 2 × 8,192³ = {flop / 1e12:.4f} × 10¹² FLOP / (0.70 × 989 × 10¹² FLOP/s) | {kern:.2f} ms |
| D2H (C) | {mat_b:,} B / 52 × 10⁹ B/s | {d2h:.2f} ms |
| Total | | {total:.2f} ms (kernel {kern / total * 100:.0f} %) |

Intensity if operands cross PCIe per use: {flop / 1e12:.4f} × 10¹² / (3 × {mat_b:,}) = {intensity:,.0f} FLOP/B, against a PCIe
ridge of 989 × 10¹² / 52 × 10⁹ = {ridge:,.0f} FLOP/B: PCIe-bound by ≈ {ridge / intensity:.1f}×.
"""
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
