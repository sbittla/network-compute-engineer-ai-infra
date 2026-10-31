#!/usr/bin/env python3
"""WP2 — 512-GPU variant: Clos sizing, ECMP idle uplinks, Young's interval at halved MTBF (Sections 24.6-24.7)."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

# (a) inputs: prompt + Section 24.7 [MODELED]
NODES = 64
RAILS = 8                    # one NIC per GPU, GPU i -> rail i
RADIX = 64                   # 64 x 400G switches
DOWN = UP = RADIX // 2       # non-blocking leaf: 32 down, 32 up
# (b) inputs: Section 24.7
UPLINKS = 32
FLOWS = (32, 128)            # 32 equal flows; 4 QPs per connection -> 128
# (c) inputs: Section 24.6 / REFERENCE_CLUSTER reliability assumptions [ILLUSTRATIVE]
NODE_MTBF_H = 768            # halved from 1,536 h
CANON_NODE_MTBF_H = 1536
JOB_NODES = 32               # ORION-256
CKPT_S = 12.25               # 980 GB at 80 GB/s
RESTART_S = 900

def write_outputs(out: Path, payload: dict, md_lines: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8", newline="\n")


def main_args() -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    return ap.parse_args().out


def young(node_mtbf_h: float) -> dict:
    m = node_mtbf_h / JOB_NODES * 3600
    tau = math.sqrt(2 * CKPT_S * m)
    ck, rw, rs = CKPT_S / tau, (tau / 2) / m, RESTART_S / m
    return {"job_mtbf_s": round(m, 1), "tau_s": round(tau, 1), "ckpt_pct": round(100 * ck, 3),
            "rework_pct": round(100 * rw, 3), "restart_pct": round(100 * rs, 3),
            "total_pct": round(100 * (ck + rw + rs), 2)}


def main() -> None:
    out = main_args()
    per_rail = NODES // DOWN
    leaves = RAILS * per_rail
    uplinks_total = leaves * UP
    spines = uplinks_total // RADIX
    per_pair = UP // spines
    host_links = NODES * RAILS
    links = host_links + uplinks_total
    a = {"leaves_per_rail": per_rail, "total_leaves": leaves, "spines": spines, "links_per_leaf_spine_pair": per_pair,
         "host_links": host_links, "fabric_links": uplinks_total, "total_links": links, "switches": leaves + spines}

    b = {}
    for f in FLOWS:
        p_idle = (1 - 1 / UPLINKS) ** f
        b[f"flows_{f}"] = {"p_idle": round(p_idle, 4), "idle_uplinks": round(UPLINKS * p_idle, 2),
                           "idle_pct": round(100 * p_idle, 1), "mean_flows_per_uplink": f / UPLINKS}
    c, c0 = young(NODE_MTBF_H), young(CANON_NODE_MTBF_H)

    assert a == {"leaves_per_rail": 2, "total_leaves": 16, "spines": 8, "links_per_leaf_spine_pair": 4,
                 "host_links": 512, "fabric_links": 512, "total_links": 1024, "switches": 24}
    assert abs(b["flows_32"]["idle_uplinks"] - 11.6) < 0.05        # key: 11.6
    assert abs(b["flows_128"]["idle_uplinks"] - 0.55) < 0.01        # key: 0.55
    assert abs(c["tau_s"] - 1455) < 1                               # key: 1,455 s
    assert abs(c["total_pct"] - 2.7) < 0.05                         # key: ~2.7 %
    assert abs(c0["tau_s"] - 2058) < 1 and abs(c0["total_pct"] - 1.7) < 0.05

    payload = {"id": "WP2", "evidence_label": "MODELED",
               "inputs": {"nodes": NODES, "rails": RAILS, "radix": RADIX, "uplinks": UPLINKS, "flows": list(FLOWS),
                          "node_mtbf_h": NODE_MTBF_H, "job_nodes": JOB_NODES, "ckpt_s": CKPT_S, "restart_s": RESTART_S},
               "steps": {"canonical_48h": c0},
               "answer": {"a_sizing": a, "b_ecmp": b, "c_young_768h": c},
               "units": {"tau": "s", "overheads": "% of cluster time"}}
    md = ["# WP2 — 512-GPU variant `[MODELED]`", "",
          f"(a) {per_rail} leaves per rail, {leaves} leaves, {spines} spines, {per_pair} links per leaf–spine pair, "
          f"{host_links} + {uplinks_total} = {links:,} links, {leaves + spines} switches",
          f"(b) 32 flows: 32 × (31/32)^32 = {b['flows_32']['idle_uplinks']} idle uplinks "
          f"({b['flows_32']['idle_pct']} %); 128 flows: {b['flows_128']['idle_uplinks']} idle uplinks",
          f"(c) M = {c['job_mtbf_s']:,.0f} s; τ = {c['tau_s']:,.1f} s; overhead {c['ckpt_pct']} + {c['rework_pct']} + "
          f"{c['restart_pct']} = {c['total_pct']} % (canonical 48 h: τ = {c0['tau_s']:,.1f} s, {c0['total_pct']} %)"]
    write_outputs(out, payload, md)


if __name__ == "__main__":
    main()
