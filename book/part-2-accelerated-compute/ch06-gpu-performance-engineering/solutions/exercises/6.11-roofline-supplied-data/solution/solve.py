"""Exercise 6.11: classify four kernels on the ORION roofline and express each as a fraction of its binding roof.

Usage: python solve.py --out DIR
Kernel table from the prompt; vendor ceilings from this package's lab/data/device.yaml (Table 6.1);
measured roofs (2.95 TB/s, 700 TFLOP/s BF16, [ILLUSTRATIVE]) from the prompt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

DEVICE = Path(__file__).resolve().parents[4] / "lab" / "data" / "device.yaml"
KERNELS = [  # name, precision key, FLOP, DRAM bytes, measured time (s)
    ("K1 softmax", "bf16_tensor", 1.0e9, 1.6e9, 0.60e-3),
    ("K2 GEMM", "bf16_tensor", 4.4e12, 0.6e9, 7.4e-3),
    ("K3 decode attention", "bf16_tensor", 8.6e9, 2.15e9, 0.75e-3),
    ("K4 reduction", "fp32_simt", 2.0e11, 0.4e9, 5.0e-3),
]
KEY = {"K1 softmax": ("memory", 0.796), "K2 GEMM": ("compute", 0.601),
       "K3 decode attention": ("memory", 0.856), "K4 reduction": ("compute", 0.597)}   # exercises-key.md 6.11
LEVER = {"K1 softmax": "fuse with neighbours to remove the pass",
         "K2 GEMM": "tile configuration / library choice; FP8 if accuracy allows",
         "K3 decode attention": "fewer bytes: KV cache precision, batching",
         "K4 reduction": "move to Tensor Cores (TF32/BF16) or restructure; FP32 SIMT roof is 15× below BF16"}
RANK = ["K4 reduction", "K2 GEMM", "K1 softmax", "K3 decode attention"]
TOL = 0.002
MEASURED = {"hbm_Bps": 2.95e12, "bf16_tensor": 700e12}   # prompt, [ILLUSTRATIVE]; FP32 not measured
KEY_MEASURED = {"K1 softmax": 0.904, "K2 GEMM": 0.849, "K3 decode attention": 0.972}   # exercises-key.md 6.11


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    d = yaml.safe_load(DEVICE.read_text(encoding="utf-8"))
    bw = float(d["hbm_bytes_per_s"])
    rows = []
    for name, prec, flop, byt, t in KERNELS:
        peak = float(d["peak_flops"][prec])
        ridge = peak / bw
        i = flop / byt
        bound = "compute" if i >= ridge else "memory"
        frac = flop / t / peak if bound == "compute" else byt / t / bw
        achieved = f"{flop / t / 1e12:.1f} TFLOP/s" if bound == "compute" else f"{byt / t / 1e12:.2f} TB/s"
        k_bound, k_frac = KEY[name]
        assert bound == k_bound and abs(frac - k_frac) < TOL, (name, bound, frac)
        m_frac = m_headroom = None
        if prec in MEASURED:
            m_roof = MEASURED["hbm_Bps"] if bound == "memory" else MEASURED[prec]
            m_frac = (byt if bound == "memory" else flop) / t / m_roof
            assert abs(m_frac - KEY_MEASURED[name]) < TOL, (name, m_frac)
            m_headroom = round(t * (1 - m_frac) * 1e3, 3)
            m_frac = round(m_frac, 4)
        rows.append({"kernel": name, "precision": prec, "I_flop_per_B": round(i, 3), "ridge_flop_per_B": round(ridge, 1),
                     "bound": bound, "achieved": achieved, "fraction_of_roof": round(frac, 4),
                     "headroom_ms": round(t * (1 - frac) * 1e3, 3), "fraction_of_measured_roof": m_frac,
                     "headroom_vs_measured_ms": m_headroom, "lever": LEVER[name]})
    res = {"exercise": "6.11", "evidence_label": "MODELED",
           "inputs": {"kernels": [list(k) for k in KERNELS], "peak_flops": {k: float(v) for k, v in d["peak_flops"].items()},
                      "hbm_Bps": bw, "measured_roofs": MEASURED},
           "answer": {"rows": rows, "ranking": RANK}, "units": {"I": "FLOP/B", "headroom": "ms"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 6.11 — roofline classification `[MODELED]`", "",
          "| Kernel | I (FLOP/B) | Ridge | Bound | Achieved | Fraction of vendor roof | Headroom at vendor roof "
          "| Fraction of measured roof | Headroom at measured roof |", "|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {r['kernel']} | {r['I_flop_per_B']:,.3f} | {r['ridge_flop_per_B']:.0f} | {r['bound']} | {r['achieved']} | "
           f"{r['fraction_of_roof'] * 100:.1f} % | {r['headroom_ms']:.2f} ms | "
           + ("not measured | — |" if r["fraction_of_measured_roof"] is None else
              f"{r['fraction_of_measured_roof'] * 100:.1f} % | {r['headroom_vs_measured_ms']:.2f} ms |") for r in rows]
    md += ["", "Ranking by opportunity: " + " > ".join(RANK) + " (unchanged by the measured roofs; K2's tuning "
           "headroom shrinks from 2.95 ms to 1.11 ms, K1 and K3 are effectively at the roof)."]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
