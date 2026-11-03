#!/usr/bin/env python3
"""2.10: option arithmetic for growing ORION to 64 HX8 nodes in the same row.

Usage: python solve.py --out DIR
Facility envelope from lab/data/facility_envelope.yaml; DLC node 9.138 kW from Exercise 2.6; other
assumptions from the prompt [ILLUSTRATIVE]. Network power for the doubled fabric is assumed 64 kW.
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

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
NODES, RAILS, LEAF_PORTS, SPINE_PORTS = 64, 8, 64, 64
POSITIONS_MAX, IT_MAX_KW, CDUS, CDU_KW = 13 + 6, 800.0, 2, 300.0
SUPPORT = {"network": 64.0, "storage": 18.0, "management": 4.0}
SUPPORT_RACKS = {"A": 5, "B": 5, "C": 3}           # C: management folded into network, storage in one rack
NODE_KW = {"air": 10.2, "dlc": 8590 / 0.94 / 1000}
CAPTURE = {"air": 0.75, "dlc": 0.80}
NODE_KG, NON_NODE_KG, AUX_KW, AMPS = 135, 280, 0.2, 60
OPTIONS = {"A": ("air", 4), "B": ("dlc", 5), "C": ("dlc", 4)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    env = yaml.safe_load((DATA / "facility_envelope.yaml").read_text(encoding="utf-8"))
    el, st = env["electrical"], env["structural"]
    usable_side = 2 * math.sqrt(3) * el["circuit_voltage_v"] * AMPS * el["continuous_load_derate"] * el["power_factor"] / 1e3
    res = {}
    for name, (cool, per) in OPTIONS.items():
        racks = math.ceil(NODES / per)
        rack_kw = per * NODE_KW[cool] + AUX_KW
        load = NODES * NODE_KW[cool] + racks * AUX_KW   # price the 64 nodes actually installed (B's last rack holds 4)
        it = load + sum(SUPPORT.values())
        liquid = CAPTURE[cool] * load
        floor = (per * NODE_KG + NON_NODE_KG) / st["rack_footprint_m2"]
        r = {"gpu_racks": racks, "positions": racks + SUPPORT_RACKS[name], "rack_kw": rack_kw,
             "side_kw": rack_kw * (1 + el["transient_margin"]), "it_kw": it, "liquid_kw": liquid,
             "cdu_fraction": liquid / (CDUS * CDU_KW), "floor": floor,
             "residual_air_kw": (1 - CAPTURE[cool]) * rack_kw}
        r["fits"] = (r["positions"] <= POSITIONS_MAX and it <= IT_MAX_KW and r["cdu_fraction"] <= 0.9
                     and floor <= st["floor_rating_kg_per_m2"] and r["side_kw"] <= usable_side)
        res[name] = r
    leaves = RAILS * math.ceil(NODES / (LEAF_PORTS // 2))
    host_links = NODES * RAILS
    uplinks = leaves * (LEAF_PORTS // 2)
    spines = uplinks // SPINE_PORTS
    fabric = {"leaves": leaves, "spines": spines, "switches": leaves + spines, "host_links": host_links,
              "leaf_spine_links": uplinks, "links": host_links + uplinks, "link_ends": 2 * (host_links + uplinks),
              "uplinks_per_leaf_per_spine": (LEAF_PORTS // 2) // spines, "bisection_tbps": NODES * 8 * 400 / 2 / 1000}
    c = res["C"]
    assert [n for n, r in res.items() if r["fits"]] == ["C"], {n: r["fits"] for n, r in res.items()}
    assert res["A"]["positions"] > POSITIONS_MAX and res["B"]["floor"] > st["floor_rating_kg_per_m2"]
    assert abs(c["rack_kw"] - 36.75) < 0.01 and abs(c["liquid_kw"] - 470.4) < 0.1 and abs(c["cdu_fraction"] - 0.784) < 0.001
    assert abs(c["floor"] - 1138.9) < 0.1 and c["it_kw"] < IT_MAX_KW and c["positions"] == 19
    assert fabric == {"leaves": 16, "spines": 8, "switches": 24, "host_links": 512, "leaf_spine_links": 512,
                      "links": 1024, "link_ends": 2048, "uplinks_per_leaf_per_spine": 4, "bisection_tbps": 102.4}
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] assumptions",
              "answer": {"options": {n: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}
                                     for n, r in res.items()}, "chosen": "C", "fabric": fabric},
              "units": {"power": "kW", "floor": "kg/m2"}}
    md = ["# 2.10 `[MODELED]`", "", "| Option | GPU racks | Positions | IT kW | Liquid kW | CDU | Floor | Fits |",
          "|---|---:|---:|---:|---:|---:|---:|---|"]
    for n, r in res.items():
        md.append(f"| {n} | {r['gpu_racks']} | {r['positions']} | {r['it_kw']:.0f} | {r['liquid_kw']:.1f} | "
                  f"{r['cdu_fraction']:.1%} | {r['floor']:.0f} | {r['fits']} |")
    md += ["", f"Fabric: {fabric}"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
