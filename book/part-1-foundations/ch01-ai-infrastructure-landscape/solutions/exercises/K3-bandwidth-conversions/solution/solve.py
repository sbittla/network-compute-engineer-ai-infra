#!/usr/bin/env python3
"""K3: bandwidth unit conversions for ORION.

Usage: python solve.py --out DIR
Inputs: docs/REFERENCE_CLUSTER.md (400 Gb/s NICs, NVLink 900 GB/s bidirectional, 8 NICs per node).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def house(line: str) -> str:
    """Apply the book's copyedit house style to generated Markdown (x -> ×, ~ -> ≈, '40 %', µs)."""
    line = re.sub(r"(\d)%", r"\1 %", line)
    line = line.replace(" x ", " × ")
    line = re.sub(r"(\d)x\b", r"\1×", line)
    line = re.sub(r"~ ?", "≈ ", line)
    line = re.sub(r"(\d) us\b", r"\1 µs", line)
    return line.replace("scaleout", "scale-out").replace("scaleup", "scale-up")

NIC_GBITS = 400            # Gb/s per backend NIC
NVLINK_BIDIR_GBYTES = 900  # GB/s total bidirectional per GPU
NICS_PER_NODE = 8
KEY = {"a_GBps": 50.0, "b_GBps_per_direction": 450.0, "c_Gbps": 3200.0, "c_GBps_per_direction": 400.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    ans = {"a_GBps": NIC_GBITS / 8,
           "b_GBps_per_direction": NVLINK_BIDIR_GBYTES / 2,
           "c_Gbps": NICS_PER_NODE * NIC_GBITS,
           "c_GBps_per_direction": NICS_PER_NODE * NIC_GBITS / 8}
    for k, v in KEY.items():
        assert abs(ans[k] - v) < 1e-9, (k, ans[k])
    ratio = ans["b_GBps_per_direction"] / ans["a_GBps"]
    assert ratio == 9.0
    result = {"evidence": "[MODELED] from [VENDOR-SPEC, 2026-10]-class rates", "answer": ans,
              "nvlink_to_nic_ratio_per_gpu": ratio, "units": "GB/s unless suffixed Gbps"}
    md = ["# K3 — conversions", "",
          f"- (a) {NIC_GBITS} Gb/s / 8 = {ans['a_GBps']:.0f} GB/s",
          f"- (b) {NVLINK_BIDIR_GBYTES} GB/s bidirectional / 2 = {ans['b_GBps_per_direction']:.0f} GB/s per direction",
          f"- (c) {NICS_PER_NODE} x {NIC_GBITS} Gb/s = {ans['c_Gbps']:.0f} Gb/s = {ans['c_GBps_per_direction']:.0f} GB/s per direction",
          f"- NVLink : NIC per GPU = {ratio:.0f}x"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
