"""10.M3 — Ports, cables and spares for a 24-node rail-optimized HX8 pod (and growth to 32 nodes).

Usage: python solve.py --out DIR      Evidence label: [MODELED]
Inputs: prompt parameters (24 nodes, 8 rails, 64-port switches, 1:1, DR4 everywhere) and the
spares policy in lab/data/fabrics.yaml (3 % optics, 2 % cables, min 2, 1 switch per model).
Method: Sections 10.10 and 10.12 (same logic as the lab's estimate_fabric_bom()).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
NODES = 24
RAILS = 8
RADIX = 64
OVERSUB = 1.0            # down:up = 1:1
GROWTH_NODES = 32


def bom(nodes: int, policy: dict) -> dict:
    down_max = int(RADIX * OVERSUB / (1 + OVERSUB))
    leaves_per_rail = math.ceil(nodes / down_max)
    leaves = RAILS * leaves_per_rail
    down = math.ceil(nodes / leaves_per_rail)
    up = math.ceil(down / OVERSUB)
    host_links = nodes * RAILS
    fabric_links = leaves * up
    spines = math.ceil(fabric_links / RADIX)
    while up % spines:
        spines += 1
    links = host_links + fabric_links
    optics = 2 * links
    return {
        "down_max_per_leaf": down_max, "leaves": leaves, "down_per_leaf": down, "up_per_leaf": up,
        "spines": spines, "uplinks_per_leaf_per_spine": up // spines,
        "host_links": host_links, "fabric_links": fabric_links, "total_links": links,
        "optics_dr4": optics, "cables": links,
        "leaf_ports_used": leaves * (down + up), "leaf_ports_free": leaves * RADIX - leaves * (down + up),
        "spine_ports_used": fabric_links, "spine_ports_free": spines * RADIX - fabric_links,
        "spare_optics": max(math.ceil(round(optics * policy["optic_rate"], 6)), policy["min_per_type"]),
        "spare_cables": max(math.ceil(round(links * policy["cable_rate"], 6)), policy["min_per_type"]),
        "spare_switches": policy["spare_switches_per_model"],
    }


def solve() -> dict:
    policy = yaml.safe_load((DATA / "fabrics.yaml").read_text(encoding="utf-8"))["spares_policy"]
    now, grown = bom(NODES, policy), bom(GROWTH_NODES, policy)
    return {"inputs": {"nodes": NODES, "rails": RAILS, "radix": RADIX, "oversubscription": "1:1",
                       "policy": policy},
            "answer": now, "growth_32_nodes": grown,
            "operational_spares": ["pre-imaged spare switch", "PSUs and fan trays (if field-replaceable)",
                                   "MPO jumpers in each used length", "cleaning supplies",
                                   "inspection probe tips", "labels"],
            "units": {"all": "count"}, "evidence_label": "[MODELED]"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    r = solve()
    a, g = r["answer"], r["growth_32_nodes"]
    # Answer key 10.M3 (exact integers).
    assert (a["leaves"], a["spines"], a["uplinks_per_leaf_per_spine"]) == (8, 3, 8)
    assert (a["host_links"], a["fabric_links"], a["optics_dr4"], a["cables"]) == (192, 192, 768, 384)
    assert (a["leaf_ports_used"], a["leaf_ports_free"], a["spine_ports_used"], a["spine_ports_free"]) == (384, 128, 192, 0)
    assert (a["spare_optics"], a["spare_cables"], a["spare_switches"]) == (24, 8, 1)
    assert (g["spines"], g["fabric_links"], g["uplinks_per_leaf_per_spine"], g["leaf_ports_free"]) == (4, 256, 8, 0)
    (out / "result.json").write_text(json.dumps(r, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# 10.M3 — 24-node pod BOM and spares `[MODELED]`", "", "| Quantity | 24 nodes | 32 nodes |", "|---|---|---|"]
    for k in a:
        md.append(f"| {k} | {a[k]} | {g[k]} |")
    md += ["", "Operational spares: " + "; ".join(r["operational_spares"]) + ".", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
