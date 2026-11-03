#!/usr/bin/env python3
"""DC: cost arithmetic for shared vs dedicated W-INFER capacity.

Usage: python solve.py --out DIR
Inputs: prompt ($3.00/GPU-hour, Chapter 21 TCO, 8 HX8 nodes); 60 % mean inference load [ILLUSTRATIVE].
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

NODES = 8
GPUS_PER_NODE = 8
USD_PER_GPU_HOUR = 3.00
HOURS_PER_YEAR = 8760
INFER_LOAD = 0.60
NICS_PER_NODE = 8
TOKENS_PER_NODE = 3370       # BF16 TP 8 decode, Section 1.9
KEY = {"pool_usd_year": 1_681_920, "reclaimable_usd_year": 672_768, "backend_ports_saved": 64}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    gpus = NODES * GPUS_PER_NODE
    pool = gpus * USD_PER_GPU_HOUR * HOURS_PER_YEAR
    reclaim = (1 - INFER_LOAD) * gpus * HOURS_PER_YEAR * USD_PER_GPU_HOUR
    nics = NODES * NICS_PER_NODE
    leaf_ports = nics
    optics = nics + leaf_ports
    assert abs(pool - KEY["pool_usd_year"]) < 0.01
    assert abs(reclaim - KEY["reclaimable_usd_year"]) < 0.01
    assert nics == KEY["backend_ports_saved"]
    ans = {"gpus": gpus, "pool_usd_year": round(pool, 2), "reclaimable_usd_year_upper_bound": round(reclaim, 2),
           "backend_nics_avoided": nics, "rail_leaf_ports_avoided": leaf_ports, "optics_avoided": optics,
           "pool_decode_tokens_s": NODES * TOKENS_PER_NODE}
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] cost and load", "inputs": {
        "nodes": NODES, "usd_per_gpu_hour": USD_PER_GPU_HOUR, "inference_load": INFER_LOAD}, "answer": ans,
        "units": {"cost": "USD per year", "throughput": "output tokens/s"}}
    md = ["# DC — cost arithmetic `[MODELED]`", "",
          f"- pool: {gpus} GPUs x ${USD_PER_GPU_HOUR} x {HOURS_PER_YEAR} h = ${pool:,.0f}/year",
          f"- reclaimable by sharing at {INFER_LOAD:.0%} inference load: <= ${reclaim:,.0f}/year",
          f"- dedicated pool avoids {nics} backend NICs, {leaf_ports} rail-leaf ports, {optics} optics",
          f"- pool decode capacity: {NODES * TOKENS_PER_NODE:,} tokens/s"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
