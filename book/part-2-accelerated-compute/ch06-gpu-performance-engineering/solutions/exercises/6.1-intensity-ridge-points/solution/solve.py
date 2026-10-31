"""Exercise 6.1: ridge points I* = P / B for ORION's dense BF16, FP8 and FP32 SIMT ceilings.

Usage: python solve.py --out DIR
Ceilings from this package's lab/data/device.yaml (Table 6.1, [VENDOR-SPEC, 2026-10]).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

DEVICE = Path(__file__).resolve().parents[4] / "lab" / "data" / "device.yaml"
KEY = {"bf16_tensor": 295, "fp8_tensor": 591, "fp32_simt": 20}   # exercises-key.md 6.1 (FLOP/B)
TOL = 0.5  # FLOP/B


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    d = yaml.safe_load(DEVICE.read_text(encoding="utf-8"))
    bw = float(d["hbm_bytes_per_s"])
    ridge = {k: float(v) / bw for k, v in d["peak_flops"].items()}
    for k, v in KEY.items():
        assert abs(ridge[k] - v) < TOL, (k, ridge[k])
    res = {"exercise": "6.1", "evidence_label": "MODELED (from VENDOR-SPEC ceilings)",
           "inputs": {"peak_flops": {k: float(v) for k, v in d["peak_flops"].items()}, "hbm_Bps": bw},
           "answer": {f"ridge_{k}": round(v, 1) for k, v in ridge.items()}, "units": {"ridge": "FLOP/B"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 6.1 — ridge points `[MODELED]`", "", "| Precision | Peak | Ridge = peak / 3.35 TB/s |", "|---|---|---|"]
    md += [f"| {k} | {float(d['peak_flops'][k]) / 1e12:,.0f} TFLOP/s | {v:.1f} FLOP/B |" for k, v in ridge.items()]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
