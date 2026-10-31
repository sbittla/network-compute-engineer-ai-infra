"""M4 - capacity/power/cooling model for a hall of Design-B racks.

python solve.py --out DIR.  Design-B values from the prompt and the package's lab/data/designs.yaml
[ILLUSTRATIVE]; results [MODELED].  Method (manuscript Sections 21.5-21.7):
rack provisioned kW = nodes × 14.3; liquid heat = 80 %; mass flow = P / (c_p × dT); rack limit per side
>= rack peak / (1 - transient margin) under 2N; hall nodes = min(power fit, cooling fit).
"""
import argparse
import json
import math
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
NODES_PER_RACK = 8             # prompt
KW_PER_NODE = 14.3             # prompt: provisioned
SUSTAINED_KW_PER_NODE = 12.0   # designs.yaml (Design B)
LIQUID_FRACTION = 0.80         # prompt
CP_WATER = 4.18                # kJ/(kg K)
CP_GLYCOL = 3.9                # kJ/(kg K), glycol mix (Section 21.7)
DELTA_T = 10.0                 # K, prompt
LITRES_PER_KG = 1.0            # water near room temperature (approximation)
MARGIN = 0.10                  # transient margin (ORION policy)
GPU_SWING_W = 250              # per-GPU synchronized swing assumption (Section 21.7), for scale
KEY = {"rack_kw": 114.4, "liquid_kw": 91.5, "flow_kg_s": 2.19, "flow_l_min": 131, "air_kw": 22.9,
       "hall_nodes": 62, "hall_racks": 8}
TOL = {"rack_kw": 0.05, "liquid_kw": 0.05, "flow_kg_s": 0.005, "flow_l_min": 0.6, "air_kw": 0.05}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    dz = yaml.safe_load((DATA / "designs.yaml").read_text(encoding="utf-8"))
    a = yaml.safe_load((DATA / "assumptions.yaml").read_text(encoding="utf-8"))
    b = next(d for d in dz["designs"] if d["name"].startswith("B"))
    assert b["provisioned_it_kw_per_node"] == KW_PER_NODE and b["liquid_fraction"] == LIQUID_FRACTION
    ov = a["network_storage_overhead"]

    rack_kw = NODES_PER_RACK * KW_PER_NODE
    rack_sustained_kw = NODES_PER_RACK * SUSTAINED_KW_PER_NODE
    liquid_kw = rack_kw * LIQUID_FRACTION
    air_kw = rack_kw - liquid_kw
    flow_kg_s = liquid_kw / (CP_WATER * DELTA_T)
    flow_l_min = flow_kg_s * LITRES_PER_KG * 60
    flow_glycol = liquid_kw / (CP_GLYCOL * DELTA_T)
    side_limit_needed = rack_kw / (1 - MARGIN)
    n_power = int(dz["facility_it_kw"] // (KW_PER_NODE * (1 + ov)))
    n_cool = int(dz["liquid_cooling_kw_available"] // (KW_PER_NODE * LIQUID_FRACTION))
    hall_nodes = min(n_power, n_cool)
    hall_racks = math.ceil(hall_nodes / NODES_PER_RACK)
    hall_liquid_kw = hall_nodes * KW_PER_NODE * LIQUID_FRACTION
    hall_air_kw = hall_nodes * KW_PER_NODE * (1 - LIQUID_FRACTION)
    hall_flow_kg_s = hall_liquid_kw / (CP_WATER * DELTA_T)
    hall_facility_mw = hall_nodes * SUSTAINED_KW_PER_NODE * (1 + ov) * b["pue"] / 1000
    rack_swing_kw = NODES_PER_RACK * 8 * GPU_SWING_W / 1000
    hall_swing_kw = hall_nodes * 8 * GPU_SWING_W / 1000

    got = {"rack_kw": rack_kw, "liquid_kw": liquid_kw, "flow_kg_s": flow_kg_s, "flow_l_min": flow_l_min,
           "air_kw": air_kw}
    for k, v in got.items():
        assert abs(v - KEY[k]) <= TOL[k], (k, v)
    assert hall_nodes == KEY["hall_nodes"] and n_power < n_cool, "power binds before cooling"
    assert hall_racks == KEY["hall_racks"]

    result = {"exercise": "M4", "evidence_label": "[MODELED]",
              "inputs": {"nodes_per_rack": NODES_PER_RACK, "kw_per_node": KW_PER_NODE,
                         "sustained_kw_per_node": SUSTAINED_KW_PER_NODE, "liquid_fraction": LIQUID_FRACTION,
                         "cp_water": CP_WATER, "delta_t_k": DELTA_T, "transient_margin": MARGIN,
                         "facility_it_kw": dz["facility_it_kw"], "cdu_kw": dz["liquid_cooling_kw_available"],
                         "pue": b["pue"], "gpu_swing_w": GPU_SWING_W},
              "steps": {"rack_sustained_kw": round(rack_sustained_kw, 1), "flow_glycol_kg_s": round(flow_glycol, 2),
                        "nodes_power_fit": n_power, "nodes_cooling_fit": n_cool,
                        "hall_liquid_kw": round(hall_liquid_kw, 1), "hall_air_kw": round(hall_air_kw, 1),
                        "hall_flow_kg_s": round(hall_flow_kg_s, 1), "hall_flow_l_min": round(hall_flow_kg_s * 60),
                        "hall_facility_mw": round(hall_facility_mw, 3)},
              "answer": {"rack_provisioned_kw": round(rack_kw, 1), "rack_liquid_kw": round(liquid_kw, 1),
                         "rack_air_kw": round(air_kw, 1), "rack_flow_kg_s": round(flow_kg_s, 2),
                         "rack_flow_l_min": round(flow_l_min), "per_side_limit_needed_kw": round(side_limit_needed, 1),
                         "hall_nodes": hall_nodes, "hall_racks": hall_racks,
                         "rack_transient_swing_kw": round(rack_swing_kw, 1), "hall_transient_swing_kw": round(hall_swing_kw, 1)},
              "units": {"power": "kW", "flow": "kg/s and L/min (water)", "facility": "MW"},
              "tolerance": TOL}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# M4 - Design-B hall model `[MODELED]`", "",
          f"- Rack: {NODES_PER_RACK} × {KW_PER_NODE} kW = **{rack_kw:.1f} kW** provisioned ({rack_sustained_kw:.0f} kW sustained)",
          f"- 2N: each side must carry the rack; with a {MARGIN * 100:.0f} % transient margin each side needs >= "
          f"{side_limit_needed:.1f} kW continuous",
          f"- Liquid: {LIQUID_FRACTION} × {rack_kw:.1f} = {liquid_kw:.2f} kW; air residual {air_kw:.2f} kW",
          f"- Flow: {liquid_kw:.2f} / ({CP_WATER} × {DELTA_T:.0f}) = **{flow_kg_s:.2f} kg/s = {flow_l_min:.0f} L/min** "
          f"(glycol {flow_glycol:.2f} kg/s)",
          f"- Hall: power fit {n_power} nodes, cooling fit {n_cool} -> **{hall_nodes} nodes in {hall_racks} racks**; "
          f"{hall_flow_kg_s:.1f} kg/s total, {hall_air_kw:.0f} kW to air, facility {hall_facility_mw:.3f} MW",
          f"- Transient (250 W/GPU swing): {rack_swing_kw:.0f} kW per rack, {hall_swing_kw:.0f} kW per hall", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
