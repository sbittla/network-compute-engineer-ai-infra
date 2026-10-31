#!/usr/bin/env python3
"""W1 — repair the Kestrel capstone bundle: GPU accounting, leaf ports, cables, racks [MODELED].

Usage: python solve.py --out DIR   (writes result.json and result.md; asserts the answer key)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def r(x: float, nd: int = 4) -> float:
    return round(float(x), nd)


def write(out: Path, result: dict, md_lines: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    (out / "result.md").write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")


def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol

# Inputs: exercises.md W1 (Kestrel bundle) and docs/REFERENCE_CLUSTER.md (node power model).
NODES = 34
GPUS_PER_NODE = 8
TARGET_GPUS = 256
TP, PP, DP_CLAIMED = 8, 4, 16
LEAF_RADIX = 64
LEAVES = 8               # one per rail
SPINES = 4
UPLINKS_CLAIMED = 32
CABLES_CLAIMED = 512
RACK_KW = 45.0
NODE_MAX_KW = 10.2
NODE_BASE_KW = 4.6       # REFERENCE_CLUSTER node power model: 4.6 kW + 8 x P
GPU_TDP_W = 700
RACKS_AVAILABLE = 8


def main(out: Path) -> None:
    spares = NODES * GPUS_PER_NODE // GPUS_PER_NODE - TARGET_GPUS // GPUS_PER_NODE
    dp = TARGET_GPUS // (TP * PP)
    ports_claimed = NODES + UPLINKS_CLAIMED
    max_up = LEAF_RADIX - NODES
    uplinks = max_up - max_up % SPINES
    per_spine = uplinks // SPINES
    oversub_all = NODES / uplinks
    oversub_idle = (NODES - spares) / uplinks
    spine_ports = LEAVES * per_spine
    cables = LEAVES * (NODES + uplinks)
    host_leaf, leaf_spine = LEAVES * NODES, LEAVES * uplinks
    cables_as_drawn = LEAVES * ports_claimed
    nodes_per_rack = math.floor(RACK_KW / NODE_MAX_KW)
    racks = math.ceil(NODES / nodes_per_rack)
    cap_kw = RACK_KW / 5
    gpu_cap_w = (cap_kw - NODE_BASE_KW) / GPUS_PER_NODE * 1000

    # answer key W1 (exact integers; ratios to 0.001)
    assert spares == 2 and (NODES - spares) * GPUS_PER_NODE == 256
    assert TP * PP * DP_CLAIMED == 512 and dp == 8
    assert ports_claimed == 66 and uplinks == 28 and per_spine == 7 and NODES + uplinks == 62
    assert close(oversub_all, 1.214, 0.001) and close(oversub_idle, 1.143, 0.001)
    assert spine_ports == 56 and cables == 496 and host_leaf == 272 and leaf_spine == 224
    assert cables_as_drawn == 528 and cables != CABLES_CLAIMED
    assert nodes_per_rack == 4 and racks == 9 and racks > RACKS_AVAILABLE
    assert close(cap_kw, 9.0, 1e-9) and close(gpu_cap_w, 550.0, 1e-6)

    result = {
        "id": "W1", "evidence_label": "MODELED",
        "inputs": {"nodes": NODES, "gpus_per_node": GPUS_PER_NODE, "tp": TP, "pp": PP, "dp_claimed": DP_CLAIMED,
                   "leaf_radix": LEAF_RADIX, "leaves": LEAVES, "spines": SPINES, "uplinks_claimed": UPLINKS_CLAIMED,
                   "cables_claimed": CABLES_CLAIMED, "rack_kW": RACK_KW, "node_max_kW": NODE_MAX_KW},
        "steps": {"gpus_as_listed": NODES * GPUS_PER_NODE, "parallelism_product_claimed": TP * PP * DP_CLAIMED,
                  "leaf_ports_as_drawn": ports_claimed, "max_uplinks": max_up,
                  "cables_as_drawn": cables_as_drawn, "nodes_per_rack_exact": r(RACK_KW / NODE_MAX_KW, 3)},
        "answer": {"spares": spares, "dp": dp, "uplinks": uplinks, "uplinks_per_spine": per_spine,
                   "oversub_all_active": r(oversub_all, 3), "oversub_spares_idle": r(oversub_idle, 3),
                   "spine_ports_used": spine_ports, "backend_cables": cables, "host_leaf_cables": host_leaf,
                   "leaf_spine_cables": leaf_spine, "nodes_per_rack": nodes_per_rack, "racks_needed": racks,
                   "node_cap_kW_for_5_per_rack": r(cap_kw, 2), "gpu_cap_W": r(gpu_cap_w, 1)},
        "units": {"oversub": "ratio:1", "cables": "links", "cap": "kW / W"},
    }
    md = [
        "# W1 — Kestrel repair `[MODELED]`", "",
        f"1. GPUs: ({NODES} − {spares}) × {GPUS_PER_NODE} = {(NODES - spares) * GPUS_PER_NODE}; "
        f"DP = {TARGET_GPUS} / ({TP} × {PP}) = {dp} (claimed {DP_CLAIMED} gives {TP * PP * DP_CLAIMED})",
        f"2. Leaf: {NODES} + {UPLINKS_CLAIMED} = {ports_claimed} > {LEAF_RADIX}; uplinks ≤ {max_up}, "
        f"multiple of {SPINES} → {uplinks} ({per_spine} per spine)",
        f"   - oversubscription {NODES}:{uplinks} = {oversub_all:.3f}:1; spares idle "
        f"{NODES - spares}:{uplinks} = {oversub_idle:.3f}:1",
        f"   - spine ports {LEAVES} × {per_spine} = {spine_ports} of 64; cables {LEAVES} × ({NODES} + {uplinks}) = "
        f"{cables} ({host_leaf} + {leaf_spine}); as drawn {cables_as_drawn}; bundle says {CABLES_CLAIMED}",
        f"3. Racks: floor({RACK_KW} / {NODE_MAX_KW}) = {nodes_per_rack} per rack → ceil({NODES} / {nodes_per_rack}) = "
        f"{racks} racks; 5-node cap {cap_kw:.1f} kW → GPU cap ({cap_kw:.1f} − {NODE_BASE_KW}) / 8 = {gpu_cap_w:.0f} W",
    ]
    write(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    main(ap.parse_args().out)
