"""7.W1 — Rail-optimized two-tier backend for ORION-384 (1:1 and 3:1), versus the lab's size_two_tier.

Usage: python solve.py --out DIR

Prompt parameters: 48 HX8 nodes, 8 x 400G backend NICs per node (one per rail), 64-port 400G
switches for leaves and spines. Part (b) calls the reference size_two_tier (solutions/lab/fabric_lab.py).
[MODELED]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lab"))
import fabric_lab  # noqa: E402

NODES, RAILS, RADIX, LINK_GBPS = 48, 8, 64, 400


def rail_optimized(oversub: float, min_spines: int = 2) -> dict:
    """Leaf/spine counts when every rail gets a whole number of leaves."""
    down = int(round(RADIX * oversub / (1 + oversub)))
    up = RADIX - down
    leaves_per_rail = math.ceil(NODES / down)
    leaves = RAILS * leaves_per_rail
    uplinks = leaves * up
    spines = max(min_spines, math.ceil(uplinks / RADIX))
    while up % spines:            # equal parallel links to every spine
        spines += 1
    links_per_pair = up // spines
    assert leaves * links_per_pair <= RADIX, "spine radix exceeded"
    endpoints = NODES * RAILS
    return {
        "down_per_leaf": down, "up_per_leaf": up, "leaves_per_rail": leaves_per_rail, "leaves": leaves,
        "nodes_per_leaf": NODES // leaves_per_rail, "spines": spines, "links_per_pair": links_per_pair,
        "spine_ports_used": leaves * links_per_pair,
        "downlinks_used": endpoints, "downlinks_total": leaves * down,
        "downlink_use_pct": round(100 * endpoints / (leaves * down), 1),
        "ratio_configured": f"{down // math.gcd(down, up)}:{up // math.gcd(down, up)}",
        "ratio_used": round((NODES // leaves_per_rail) / up, 2),
        "host_cables": endpoints, "fabric_cables": uplinks, "total_cables": endpoints + uplinks,
        "transceivers": 2 * (endpoints + uplinks),
        "cross_leaf_tbps": up * LINK_GBPS / 1000, "downlink_tbps": down * LINK_GBPS / 1000,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    a = rail_optimized(1.0)
    b = fabric_lab.size_two_tier(NODES * RAILS, RADIX, RADIX, 1.0)
    c = rail_optimized(3.0)

    # Key (solutions/exercises-key.md 7.W1); all exact integers.
    assert (a["leaves_per_rail"], a["leaves"], a["spines"], a["links_per_pair"]) == (2, 16, 8, 4)
    assert (a["downlinks_used"], a["downlinks_total"], a["downlink_use_pct"]) == (384, 512, 75.0)
    assert (a["ratio_configured"], a["ratio_used"]) == ("1:1", 0.75)
    assert (a["host_cables"], a["fabric_cables"], a["total_cables"], a["transceivers"]) == (384, 512, 896, 1792)
    assert (b["leaves"], b["spines"], b["links_per_leaf_spine"], b["fabric_cables"], b["total_cables"],
            b["transceivers"]) == (12, 8, 4, 384, 768, 1536)
    assert (c["leaves"], c["spines"], c["links_per_pair"], c["total_cables"], c["transceivers"]) == (8, 2, 8, 512, 1024)
    assert abs(c["cross_leaf_tbps"] - 6.4) < 1e-9 and abs(c["downlink_tbps"] - 19.2) < 1e-9

    nics_per_rail_over_down = NODES / b["down_per_leaf"]   # 1.5 leaves per rail if packed densely
    result = {
        "exercise": "7.W1", "evidence_label": "[MODELED]",
        "inputs": {"nodes": NODES, "rails": RAILS, "switch_radix": RADIX, "link_gbps": LINK_GBPS},
        "answer": {"a_rail_optimized_1to1": a, "b_size_two_tier": b, "c_rail_optimized_3to1": c},
        "steps": {"b_dense_leaves_per_rail": nics_per_rail_over_down,
                  "b_why_differs": "size_two_tier packs 384 endpoints into ceil(384/32) = 12 leaves; "
                                   "48 NICs per rail need 1.5 leaves, so a rail-optimized design rounds up to 2 per rail"},
        "units": "counts; capacities in Tb/s", "tolerance": "exact",
    }
    md = f"""# 7.W1 — result `[MODELED]`

| Quantity | (a) rail-optimized 1:1 | (b) `size_two_tier(384, 64, 64, 1.0)` | (c) rail-optimized 3:1 |
|---|---|---|---|
| Down / up per leaf | {a['down_per_leaf']} / {a['up_per_leaf']} | {b['down_per_leaf']} / {b['up_per_leaf']} | {c['down_per_leaf']} / {c['up_per_leaf']} |
| Leaves (per rail) | {a['leaves']} ({a['leaves_per_rail']}) | {b['leaves']} (not rail-aware) | {c['leaves']} ({c['leaves_per_rail']}) |
| Spines | {a['spines']} | {b['spines']} | {c['spines']} |
| Links per leaf-spine pair | {a['links_per_pair']} | {b['links_per_leaf_spine']} | {c['links_per_pair']} |
| Downlinks used / total | {a['downlinks_used']} / {a['downlinks_total']} ({a['downlink_use_pct']} %) | — | {c['downlinks_used']} / {c['downlinks_total']} |
| Host + fabric cables | {a['host_cables']} + {a['fabric_cables']} = {a['total_cables']} | {b['host_cables']} + {b['fabric_cables']} = {b['total_cables']} | {c['host_cables']} + {c['fabric_cables']} = {c['total_cables']} |
| Transceivers (before spares) | {a['transceivers']:,} | {b['transceivers']:,} | {c['transceivers']:,} |

(a) ratio {a['ratio_configured']} as configured, {a['ratio_used']}:1 as used. (c) cross-leaf {c['cross_leaf_tbps']} Tb/s vs downlink {c['downlink_tbps']} Tb/s per leaf.
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("7.W1 ok")


if __name__ == "__main__":
    main()
