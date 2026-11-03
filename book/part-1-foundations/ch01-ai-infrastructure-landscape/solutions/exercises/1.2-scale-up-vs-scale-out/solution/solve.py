#!/usr/bin/env python3
"""Exercise 1.2: ceiling-model lower bounds for two workloads on ORION.

Usage: python solve.py --out DIR
Inputs are the prompt's per-GPU profiles [ILLUSTRATIVE]; ceilings are ORION per-GPU peaks
(docs/REFERENCE_CLUSTER.md, [VENDOR-SPEC, 2026-10] class).
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

PEAK_TFLOPS = 989.0      # BF16 dense, TFLOP/s per GPU
HBM_GBPS = 3350.0        # GB/s per GPU
NVLINK_GBPS = 450.0      # GB/s per direction per GPU
NIC_GBPS = 400 / 8       # 400 Gb/s line rate -> 50 GB/s

WORKLOADS = {  # from the exercise table
    "A": {"tflop": 0.56, "hbm_gb": 20.18, "nvlink_gb": 0.147, "nic_gb": 0.0, "observed_s": 9.5e-3},
    "B": {"tflop": 400.0, "hbm_gb": 500.0, "nvlink_gb": 40.0, "nic_gb": 30.0, "observed_s": 1.5},
}
KEY = {  # solutions/exercises-key.md, Exercise 1.2
    "A": {"compute": 0.566e-3, "memory": 6.02e-3, "scaleup": 0.327e-3, "scaleout": 0.0,
          "dominant": "memory", "fraction": 0.63},
    "B": {"compute": 0.404, "memory": 0.149, "scaleup": 0.089, "scaleout": 0.600,
          "dominant": "scaleout", "fraction": 0.40},
}
REL_TOL = 0.01   # 1 % on each bound
ABS_TOL_FRACTION = 0.005


def bounds(w: dict) -> dict:
    return {
        "compute": w["tflop"] / PEAK_TFLOPS,
        "memory": w["hbm_gb"] / HBM_GBPS,
        "scaleup": w["nvlink_gb"] / NVLINK_GBPS,
        "scaleout": w["nic_gb"] / NIC_GBPS,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] profiles and [VENDOR-SPEC, 2026-10]-class ceilings",
              "ceilings": {"compute_tflops": PEAK_TFLOPS, "hbm_gbps": HBM_GBPS,
                           "nvlink_gbps": NVLINK_GBPS, "nic_gbps": NIC_GBPS},
              "inputs": WORKLOADS, "units": "seconds", "answer": {}}
    md = ["# Exercise 1.2 — lower bounds `[MODELED]`", "",
          "| Workload | Compute (s) | Memory (s) | Scale-up (s) | Scale-out (s) | Dominant | Ceiling fraction |",
          "|---|---:|---:|---:|---:|---|---:|"]
    for name, w in WORKLOADS.items():
        b = bounds(w)
        dom = max(b, key=b.get)
        frac = b[dom] / w["observed_s"]
        k = KEY[name]
        for res in ("compute", "memory", "scaleup", "scaleout"):
            assert abs(b[res] - k[res]) <= REL_TOL * max(k[res], 1e-9) + 1e-9, (name, res, b[res])
        assert dom == k["dominant"], (name, dom)
        assert abs(frac - k["fraction"]) <= ABS_TOL_FRACTION, (name, frac)
        result["answer"][name] = {"bounds_s": {r: round(v, 6) for r, v in b.items()},
                                  "dominant": dom, "ceiling_fraction": round(frac, 3)}
        md.append(f"| {name} | {b['compute']:.6f} | {b['memory']:.6f} | {b['scaleup']:.6f} | "
                  f"{b['scaleout']:.6f} | {dom} | {frac:.2f} |")
    nvlink_only_b = (WORKLOADS["B"]["nvlink_gb"] + WORKLOADS["B"]["nic_gb"]) / NVLINK_GBPS
    assert abs(nvlink_only_b - 0.156) < 0.001
    result["answer"]["B_if_all_to_all_on_nvlink_s"] = round(nvlink_only_b, 4)
    md += ["", f"If B's 30 GB moved to NVLink (on top of its 40 GB): (40 + 30) / 450 = {nvlink_only_b:.3f} s, "
           f"so B becomes compute-bound "
           f"at {bounds(WORKLOADS['B'])['compute']:.3f} s."]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
