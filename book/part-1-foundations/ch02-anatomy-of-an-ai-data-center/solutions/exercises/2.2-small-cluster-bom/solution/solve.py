#!/usr/bin/env python3
"""2.2: ORION-128 BOM from the exercise's stated assumptions.

Usage: python solve.py --out DIR
All inputs are the prompt's [ILLUSTRATIVE] assumptions (named constants below).
"""
from __future__ import annotations

import argparse
import json
import re
import math
from pathlib import Path


def house(line: str) -> str:
    """Apply the book's copyedit house style to generated Markdown (x -> ×, ~ -> ≈, '40 %', µs)."""
    line = re.sub(r"(\d)%", r"\1 %", line)
    line = line.replace(" x ", " × ")
    line = re.sub(r"(\d)x\b", r"\1×", line)
    line = re.sub(r"~ ?", "≈ ", line)
    line = re.sub(r"(\d) us\b", r"\1 µs", line)
    return line.replace("scaleout", "scale-out").replace("scaleup", "scale-up")

GPUS, GPUS_PER_NODE = 128, 8
NODE_KW, AUX_KW, NODE_U = 10.2, 0.2, 8
VOLTS, AMPS, CIRCUITS_PER_SIDE, DERATE, PF, MARGIN = 415, 32, 2, 0.80, 0.95, 0.10
RAILS, NIC_GBPS, LEAF_PORTS, SPINE_PORTS = 8, 400, 64, 64
FE_PORTS_PER_NODE = 2
OOB_FIXED = {"storage_servers": 4, "frontend_leaves": 2}
PDUS_PER_GPU_RACK = 4
KEY = {"nodes_per_rack": 3, "gpu_racks": 6, "u_per_full_rack": 24, "leaves": 8, "spines": 2,
       "host_links": 128, "leaf_spine_links": 128, "ports_used": 384, "leaf_ports_unused": 256,
       "transceivers": 512, "bisection_tbps": 25.6, "frontend_ports": 32, "oob_ports": 56}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    kw_circuit = math.sqrt(3) * VOLTS * AMPS * DERATE * PF / 1e3
    kw_side = CIRCUITS_PER_SIDE * kw_circuit
    need = {n: (NODE_KW * n + AUX_KW) * (1 + MARGIN) for n in range(1, 6)}
    nodes_per_rack = max(n for n, v in need.items() if v <= kw_side)
    nodes = GPUS // GPUS_PER_NODE
    racks = math.ceil(nodes / nodes_per_rack)
    leaves = RAILS
    down_per_leaf = nodes
    host_links = nodes * RAILS
    uplinks_per_leaf = down_per_leaf                     # 1:1
    leaf_spine = leaves * uplinks_per_leaf
    spines = math.ceil(leaf_spine / SPINE_PORTS)
    assert leaf_spine % spines == 0 and (leaf_spine // spines) % leaves == 0   # equal uplinks to every spine
    ports_used = leaves * (down_per_leaf + uplinks_per_leaf) + leaf_spine
    leaf_unused = leaves * LEAF_PORTS - leaves * (down_per_leaf + uplinks_per_leaf)
    transceivers = 2 * (host_links + leaf_spine)
    bisection = GPUS * NIC_GBPS / 2 / 1000
    fe = nodes * FE_PORTS_PER_NODE
    oob = nodes + (leaves + spines) + OOB_FIXED["frontend_leaves"] + OOB_FIXED["storage_servers"] + racks * PDUS_PER_GPU_RACK
    ans = {"kw_per_circuit": round(kw_circuit, 3), "kw_per_side": round(kw_side, 3),
           "need_kw_3": round(need[3], 3), "need_kw_4": round(need[4], 3),
           "headroom_kw_3": round(kw_side - need[3], 3), "nodes": nodes,
           "nodes_per_rack": nodes_per_rack, "gpu_racks": racks, "u_per_full_rack": nodes_per_rack * NODE_U,
           "leaves": leaves, "spines": spines, "uplinks_per_leaf_per_spine": uplinks_per_leaf // spines,
           "host_links": host_links, "leaf_spine_links": leaf_spine, "ports_used": ports_used,
           "leaf_ports_unused": leaf_unused, "transceivers": transceivers, "bisection_tbps": bisection,
           "frontend_ports": fe, "oob_ports": oob}
    for k, v in KEY.items():
        assert abs(ans[k] - v) < 1e-9, (k, ans[k], v)
    assert abs(ans["kw_per_side"] - 34.96) < 0.01 and abs(ans["headroom_kw_3"] - 1.08) < 0.01
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] assumptions", "answer": ans,
              "units": {"power": "kW", "bisection": "Tb/s per direction"}}
    md = ["# 2.2 — ORION-128 BOM `[MODELED]`", "", "| Item | Value |", "|---|---:|"]
    md += [f"| {k} | {v} |" for k, v in ans.items()]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
