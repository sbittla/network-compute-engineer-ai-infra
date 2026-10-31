#!/usr/bin/env python3
"""D1 — backend options for a 48-node ORION: leaves, spines, cables, racks, power [MODELED].

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

# Inputs: exercises.md D1; ORION spine radix 64 and rack/node power from docs/REFERENCE_CLUSTER.md.
NODES = 48
RAILS = 8
SPINE_RADIX = 64
RACK_KW = 45.0
NODE_MAX_KW = 10.2
ASIC_GBPS = 51200
PORT_GBPS = 400
OPTIONS = {   # name: (leaves per rail, leaf radix, downlinks per leaf, uplinks per leaf, spines chosen)
    "A": (1, 64, 48, 16, 4),
    "B": (2, 64, 24, 24, 6),
    "C": (1, 128, 48, 48, 6),
}


def main(out: Path) -> None:
    res = {}
    for name, (lpr, radix, down, up, spines) in OPTIONS.items():
        leaves = RAILS * lpr
        assert down * lpr == NODES                     # every node's NIC r lands on rail r
        assert down + up <= radix
        total_up = leaves * up
        assert total_up % spines == 0 and up % spines == 0
        per_spine = up // spines
        spine_ports = leaves * per_spine
        assert spine_ports <= SPINE_RADIX
        res[name] = {"leaves": leaves, "leaf_ports_used": down + up, "leaf_radix": radix,
                     "oversub": r(down / up, 3), "spines": spines, "links_per_leaf_spine": per_spine,
                     "spine_ports_used": spine_ports, "backend_cables": leaves * (down + up),
                     "host_leaf_cables": leaves * down, "leaf_spine_cables": total_up,
                     "same_rail_crosses_spine": lpr > 1}
    racks = math.ceil(NODES / math.floor(RACK_KW / NODE_MAX_KW))
    power_kw = NODES * NODE_MAX_KW
    ports_at_400g = ASIC_GBPS // PORT_GBPS

    # answer key Section E
    assert res["A"]["oversub"] == 3.0 and res["A"]["backend_cables"] == 512 and res["A"]["spine_ports_used"] == 32
    assert res["B"]["oversub"] == 1.0 and res["B"]["backend_cables"] == 768 and res["B"]["spine_ports_used"] == 64
    assert res["C"]["oversub"] == 1.0 and res["C"]["backend_cables"] == 768 and res["C"]["spine_ports_used"] == 64
    assert res["B"]["leaves"] == 16 and res["C"]["links_per_leaf_spine"] == 8
    assert racks == 12 and close(power_kw, 489.6, 1e-9) and ports_at_400g == 128

    result = {"id": "D1", "evidence_label": "MODELED",
              "inputs": {"nodes": NODES, "rails": RAILS, "spine_radix": SPINE_RADIX, "rack_kW": RACK_KW,
                         "node_max_kW": NODE_MAX_KW, "options": {k: list(v) for k, v in OPTIONS.items()}},
              "steps": {"asic_ports_at_400G": ports_at_400g},
              "answer": {"options": res, "racks": racks, "gpu_node_power_kW": r(power_kw, 1),
                         "recommendation": "C if a qualified 128-port leaf exists, else A with a revisit trigger"},
              "units": {"cables": "links", "power": "kW", "oversub": "ratio:1"}}
    md = ["# D1 — ORION-384 backend options `[MODELED]`", "",
          "| Option | Leaves | Leaf ports | Oversub | Spines | Per leaf–spine | Spine ports | Cables | Same-rail via spine |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, v in res.items():
        md.append(f"| {k} | {v['leaves']} | {v['leaf_ports_used']} / {v['leaf_radix']} | {v['oversub']:g}:1 | "
                  f"{v['spines']} | {v['links_per_leaf_spine']} | {v['spine_ports_used']} / 64 | "
                  f"{v['backend_cables']} | {'yes' if v['same_rail_crosses_spine'] else 'no'} |")
    md += ["", f"Racks: ceil({NODES} / 4) = {racks}; GPU-node power {NODES} × {NODE_MAX_KW} = {power_kw:.1f} kW; "
               f"ASIC {ASIC_GBPS:,} / {PORT_GBPS} = {ports_at_400g} ports at 400G"]
    write(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    main(ap.parse_args().out)
