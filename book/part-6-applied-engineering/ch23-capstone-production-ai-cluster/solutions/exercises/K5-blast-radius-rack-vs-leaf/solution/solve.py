#!/usr/bin/env python3
"""K5 — blast radius of a rack-power and a rail-leaf failure on ORION-256 [MODELED].

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

# Inputs: docs/REFERENCE_CLUSTER.md (ORION-256) and manuscript Table 23.5 / 23.6.
NODES = 32               # HX8 nodes
GPUS_PER_NODE = 8
RAILS = 8                # one rail leaf per rail; leaf r connects NIC r of every node
RACK_BUDGET_KW = 45.0    # planned per rack: 50 kW limit x 0.9 transient margin (A-09)
NODE_MAX_KW = 10.2       # node maximum power
LEAF_UPLINKS = 32
SPINES = 4


def main(out: Path) -> None:
    gpus = NODES * GPUS_PER_NODE
    nodes_per_rack = math.floor(RACK_BUDGET_KW / NODE_MAX_KW)
    rack_gpus = nodes_per_rack * GPUS_PER_NODE
    rack_pct = 100 * rack_gpus / gpus
    leaf_gpus_lost = 0
    leaf_nodes_hit = NODES
    leaf_bw_fraction_pct = 100 / RAILS
    spine_uplinks_left = LEAF_UPLINKS - LEAF_UPLINKS // SPINES
    spine_oversub = 32 / spine_uplinks_left

    assert nodes_per_rack == 4
    assert rack_gpus == 32 and close(rack_pct, 12.5, 1e-9)          # key K5 (a)
    assert leaf_gpus_lost == 0 and leaf_nodes_hit == 32             # key K5 (b)
    assert close(spine_oversub, 1.333, 0.001)                       # Section 23.5 contrast

    result = {
        "id": "K5", "evidence_label": "MODELED",
        "inputs": {"nodes": NODES, "gpus_per_node": GPUS_PER_NODE, "rails": RAILS,
                   "rack_budget_kW": RACK_BUDGET_KW, "node_max_kW": NODE_MAX_KW},
        "steps": {"nodes_per_rack": nodes_per_rack, "total_gpus": gpus,
                  "spine_failure_uplinks_left": spine_uplinks_left, "spine_failure_oversub": r(spine_oversub, 3)},
        "answer": {"rack_power": {"gpus_lost": rack_gpus, "pct_capacity": r(rack_pct, 2),
                                  "jobs_affected": "jobs with ranks in that rack"},
                   "rail_leaf": {"gpus_lost": leaf_gpus_lost, "nodes_losing_a_rail": leaf_nodes_hit,
                                 "backend_bw_lost_per_node_pct": r(leaf_bw_fraction_pct, 2),
                                 "jobs_affected": "every multi-node job using the rail (plan job-fatal)"}},
        "units": {"gpus_lost": "GPUs", "pct_capacity": "%", "backend_bw_lost_per_node_pct": "%"},
    }
    md = [
        "# K5 — blast radius `[MODELED]`", "",
        f"- Nodes per rack = floor({RACK_BUDGET_KW} / {NODE_MAX_KW}) = {nodes_per_rack}",
        f"- Rack power failure: {nodes_per_rack} × {GPUS_PER_NODE} = {rack_gpus} GPUs = {rack_pct:.1f} % of {gpus}",
        f"- Rail-leaf failure: {leaf_gpus_lost} GPUs lost; {leaf_nodes_hit} nodes each lose 1 of {RAILS} rails "
        f"({leaf_bw_fraction_pct:.1f} % of backend bandwidth); every multi-node job on the rail is hit",
        f"- Contrast, spine failure: uplinks 32 → {spine_uplinks_left}, oversubscription {spine_oversub:.2f}:1",
    ]
    write(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    main(ap.parse_args().out)
