#!/usr/bin/env python3
"""2.1.1: space vs power for an ORION GPU rack.

Usage: python solve.py --out DIR
Facility values read from the package's lab/data/facility_envelope.yaml; node values from
docs/REFERENCE_CLUSTER.md and manuscript Section 2.2 (10.2 kW max, 8U, 135 kg).
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
NODE_KW, NODE_U, NODE_KG = 10.2, 8, 135
AUX_KW, RACK_U, SWITCH_U, NON_NODE_KG = 0.2, 48, 3, 280
AMPS, CIRCUITS_PER_SIDE = 60, 2
ROOM_AIR_KW = 12.0          # Section 2.10 envelope
RACKS = 8
KEY = {"free_u": 13, "kw_4": 41.0, "kw_5": 51.2, "side_5": 56.3, "usable_side": 65.55}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    env = yaml.safe_load((DATA / "facility_envelope.yaml").read_text(encoding="utf-8"))
    el, co, st = env["electrical"], env["cooling"], env["structural"]
    circuit_kw = math.sqrt(3) * el["circuit_voltage_v"] * AMPS * el["continuous_load_derate"] * el["power_factor"] / 1e3
    usable_side = CIRCUITS_PER_SIDE * circuit_kw
    free_u = RACK_U - 4 * NODE_U - SWITCH_U
    kw = {n: n * NODE_KW + AUX_KW for n in (4, 5)}
    side5 = kw[5] * (1 + el["transient_margin"])
    liquid5 = co["liquid_capture_fraction"] * kw[5]
    cdu5 = RACKS * liquid5 / co["cdu_capacity_kw"]
    air5 = kw[5] - liquid5
    floor5 = (5 * NODE_KG + NON_NODE_KG) / st["rack_footprint_m2"]
    assert free_u == KEY["free_u"] and abs(kw[4] - KEY["kw_4"]) < 1e-9 and abs(kw[5] - KEY["kw_5"]) < 1e-9
    assert abs(side5 - KEY["side_5"]) < 0.05 and abs(usable_side - KEY["usable_side"]) < 0.01
    assert side5 < usable_side and cdu5 > 1.0 and air5 > ROOM_AIR_KW and floor5 > st["floor_rating_kg_per_m2"]
    ans = {"free_u_at_4_nodes": free_u, "rack_kw_4_nodes": kw[4], "rack_kw_5_nodes": round(kw[5], 2),
           "design_kw_per_side_5_nodes": round(side5, 2), "usable_kw_per_side": round(usable_side, 2),
           "cdu_load_fraction_5_nodes": round(cdu5, 3), "residual_air_kw_5_nodes": round(air5, 2),
           "floor_kg_m2_5_nodes": round(floor5, 0)}
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] inputs", "answer": ans,
              "units": {"power": "kW", "space": "U", "floor": "kg/m2"}}
    md = ["# 2.1.1 `[MODELED]`", "", f"- free space with 4 nodes: {free_u}U (a fifth 8U node fits)",
          f"- 4 nodes {kw[4]:.1f} kW; 5 nodes {kw[5]:.1f} kW = {side5:.1f} kW per side with margin (usable {usable_side:.2f})",
          f"- 5 nodes: CDU {cdu5:.0%} of {co['cdu_capacity_kw']} kW, residual air {air5:.1f} kW (room {ROOM_AIR_KW}), "
          f"floor {floor5:.0f} kg/m2 (rated {st['floor_rating_kg_per_m2']})"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
