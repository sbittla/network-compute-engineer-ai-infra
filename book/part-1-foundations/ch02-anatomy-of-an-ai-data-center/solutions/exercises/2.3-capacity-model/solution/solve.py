#!/usr/bin/env python3
"""2.3: simplified capacity model for ORION-128 (formulas visible).

Usage: python solve.py --out DIR
Inputs: the exercise's [ILLUSTRATIVE] assumptions plus ORION-128 from Exercise 2.2.
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

NODES, GPUS_PER_NODE, HBM_GB = 16, 8, 80
RESERVE = 0.10
PARAMS, STATE_B, CKPT_B, TP, PP = 13e9, 16, 14, 8, 1
STORAGE_SERVERS, READ_PER, WRITE_PER = 4, 20.0, 10.0
BISECTION_TBPS = 25.6                     # Exercise 2.2
NODE_KW, AUX_KW = 10.2, 0.2
RACK_LAYOUT = [3, 3, 3, 3, 3, 1]          # nodes per GPU rack (balanced alternative: [3, 3, 3, 3, 2, 2])
NON_GPU_KW = {"network": 10.0, "storage": 4.5, "management": 3.0}
PUE, ALLOCATION, MFU, GOODPUT, HOURS = 1.30, 0.80, 0.38, 0.92, 8760
KEY = {"gpus": 128, "hbm_total_GB": 10240, "hbm_usable_GB": 9216, "state_per_gpu_GB": 26.0,
       "read_GBps": 80, "write_GBps": 40, "read_per_gpu_GBps": 0.625, "ckpt_GB": 182, "ckpt_s": 4.55,
       "it_max_kW": 181.9, "facility_kW": 236.5, "allocated_gpu_h": 897_024, "durable_fraction": 0.28}


def rack_kw(layout: list[int]) -> float:
    return sum(n * NODE_KW + AUX_KW for n in layout)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    gpus = NODES * GPUS_PER_NODE
    m = {"gpus": gpus, "hbm_total_GB": gpus * HBM_GB, "hbm_usable_GB": gpus * HBM_GB * (1 - RESERVE),
         "usable_per_gpu_GB": HBM_GB * (1 - RESERVE), "state_per_gpu_GB": PARAMS * STATE_B / (TP * PP) / 1e9,
         "read_GBps": STORAGE_SERVERS * READ_PER, "write_GBps": STORAGE_SERVERS * WRITE_PER}
    m["state_fits"] = m["state_per_gpu_GB"] <= m["usable_per_gpu_GB"]
    m["read_per_gpu_GBps"] = m["read_GBps"] / gpus
    m["ckpt_GB"] = PARAMS * CKPT_B / 1e9
    m["ckpt_s"] = m["ckpt_GB"] / m["write_GBps"]
    m["bisection_Tbps"] = BISECTION_TBPS
    m["gpu_racks_kW"] = rack_kw(RACK_LAYOUT)
    m["gpu_racks_kW_balanced"] = rack_kw([3, 3, 3, 3, 2, 2])
    m["it_max_kW"] = m["gpu_racks_kW"] + sum(NON_GPU_KW.values())
    m["facility_kW"] = m["it_max_kW"] * PUE
    m["allocated_gpu_h"] = gpus * HOURS * ALLOCATION
    m["durable_fraction"] = ALLOCATION * MFU * GOODPUT
    m["doubled_state_per_gpu_GB"] = 2 * m["state_per_gpu_GB"]
    m["doubled_ckpt_s"] = 2 * m["ckpt_s"]
    for k, v in KEY.items():
        assert abs(m[k] - v) <= 0.0015 * v + 1e-9, (k, m[k], v)
    assert m["state_fits"] and abs(m["gpu_racks_kW"] - m["gpu_racks_kW_balanced"]) < 1e-9
    assert m["doubled_state_per_gpu_GB"] < m["usable_per_gpu_GB"] and abs(m["usable_per_gpu_GB"] - m["doubled_state_per_gpu_GB"] - 20) < 1e-9
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] assumptions",
              "answer": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()},
              "units": {"memory": "GB", "bandwidth": "GB/s", "power": "kW", "time": "s"}}
    md = ["# 2.3 — capacity model `[MODELED]`", "", "| Line | Value |", "|---|---:|"]
    md += [f"| {k} | {result['answer'][k]} |" for k in m]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
