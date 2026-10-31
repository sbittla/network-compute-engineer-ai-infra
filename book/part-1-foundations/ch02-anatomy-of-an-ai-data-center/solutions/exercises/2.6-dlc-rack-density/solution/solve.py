#!/usr/bin/env python3
"""2.6: DLC HX8 node power, 5-node rack checks against ORION's facility envelope.

Usage: python solve.py --out DIR
Facility envelope from the package's lab/data/facility_envelope.yaml; DLC assumptions from the prompt
[ILLUSTRATIVE]; node DC breakdown from manuscript Table 2.2.
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
DC_PEAK_W, FAN_AIR_W, FAN_DLC_W, PSU_EFF = 9590, 1350, 350, 0.94
CAPTURE_DLC = 0.80
NODE_KG, NON_NODE_KG, AUX_KW = 135, 280, 0.2
AMPS, CIRCUITS_PER_SIDE, RACKS_PER_CDU = 60, 2, 8
PSUS_PER_FEED, PSU_KW = 3, 3.0
M3S_TO_CFM = 2118.88
KEY = {"node_kw": 9.138, "rack4_kw": 36.75, "saving_kw": 4.25, "side5_kw": 50.48, "lpm": 55.4,
       "cfm": 1074, "cdu_kw": 293.7, "floor": 1326, "cdu4_kw": 235.2}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    env = yaml.safe_load((DATA / "facility_envelope.yaml").read_text(encoding="utf-8"))
    el, co, st = env["electrical"], env["cooling"], env["structural"]
    usable_side = CIRCUITS_PER_SIDE * math.sqrt(3) * el["circuit_voltage_v"] * AMPS * el["continuous_load_derate"] * el["power_factor"] / 1e3
    dc = DC_PEAK_W - (FAN_AIR_W - FAN_DLC_W)
    node_kw = dc / PSU_EFF / 1e3
    rack4 = 4 * node_kw + AUX_KW
    rack4_air = 4 * 10.2 + AUX_KW
    rack5 = 5 * node_kw + AUX_KW
    side5 = rack5 * (1 + el["transient_margin"])
    liquid5 = CAPTURE_DLC * rack5
    kgs = liquid5 / (co["coolant_cp_kj_per_kg_k"] * co["design_delta_t_k"])
    lpm = kgs / co["coolant_density_kg_per_l"] * 60
    air5 = rack5 - liquid5
    cfm = air5 / (co["air_cp_kj_per_kg_k"] * co["air_density_kg_per_m3"] * co["air_delta_t_k"]) * M3S_TO_CFM
    cdu = RACKS_PER_CDU * liquid5
    floor = (5 * NODE_KG + NON_NODE_KG) / st["rack_footprint_m2"]
    feed_kw = PSUS_PER_FEED * PSU_KW
    checks = {"electrical": side5 <= usable_side, "cdu": cdu <= co["cdu_capacity_kw"] * 0.9,
              "floor": floor <= st["floor_rating_kg_per_m2"], "feed_loss": dc / 1e3 <= feed_kw}
    ans = {"dc_peak_w": dc, "node_kw": node_kw, "rack4_kw": rack4, "saving_kw": rack4_air - rack4,
           "saving_pct": (rack4_air - rack4) / rack4_air, "rack5_kw": rack5, "side5_kw": side5,
           "usable_side_kw": usable_side, "liquid5_kw": liquid5, "lpm": lpm, "air5_kw": air5, "cfm": cfm,
           "cdu_kw": cdu, "cdu_fraction": cdu / co["cdu_capacity_kw"], "floor": floor,
           "feed_margin": (feed_kw - dc / 1e3) / (dc / 1e3), "cdu4_kw": RACKS_PER_CDU * CAPTURE_DLC * rack4}
    for k, v in KEY.items():
        assert abs(ans[k] - v) <= 0.002 * v, (k, ans[k], v)
    assert checks == {"electrical": True, "cdu": False, "floor": False, "feed_loss": True}, checks
    verdict = 4 if not (checks["floor"] and checks["cdu"]) else 5
    assert verdict == 4
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] inputs",
              "answer": {**{k: round(v, 4) for k, v in ans.items()}, "checks_5_nodes": checks,
                         "nodes_per_rack_verdict": verdict, "binding": "floor (then CDU)"},
              "units": {"power": "kW", "flow": "L/min", "air": "CFM", "floor": "kg/m2"}}
    md = ["# 2.6 `[MODELED]`", "", f"- DLC node {node_kw:.3f} kW; 4-node rack {rack4:.2f} kW (saves {ans['saving_kw']:.2f} kW)",
          f"- 5 nodes: {rack5:.2f} kW, {side5:.2f} kW per side of {usable_side:.2f}",
          f"- coolant {lpm:.1f} L/min, air {cfm:.0f} CFM, CDU {cdu:.1f} kW ({ans['cdu_fraction']:.1%})",
          f"- floor {floor:.0f} kg/m2; feed loss margin {ans['feed_margin']:.1%}",
          f"- checks: {checks}; verdict {verdict} nodes per rack"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
