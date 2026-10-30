"""ORION capacity, BOM, power/cooling and failure-domain model (REFERENCE SOLUTION).

Chapter 2 lab. Every output is [MODELED] from the input sheets in ``lab/data``; none of
it is a measurement. Units are carried in key names (``_kw``, ``_gb``, ``_lpm`` ...).

Formulas used (see manuscript Sections 2.5-2.8):
  * three-phase apparent power  S = sqrt(3) x V_LL x I              (VA)
  * usable circuit power        P = S x derate x PF                  (W)
  * heat to liquid / air        Q = m_dot x cp x dT                  (kW = kg/s x kJ/(kg K) x K)
  * volumetric flow             V_dot = m_dot / rho
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import yaml

M3S_TO_CFM = 2118.88  # 1 m^3/s = 2118.88 ft^3/min

Finding = dict[str, str]


# ----------------------------------------------------------------------------- loading
def load_inputs(data_dir: Path) -> dict[str, Any]:
    """Load every input sheet from ``data_dir`` into plain Python structures.

    Returns a dict with keys ``intent``, ``facility``, ``storage``, ``design`` (YAML
    dicts) and ``racks``, ``fabric`` (lists of row dicts with numeric fields converted).
    """
    data_dir = Path(data_dir)

    def y(name: str) -> dict:
        return yaml.safe_load((data_dir / name).read_text(encoding="utf-8"))

    def rows(name: str) -> list[dict]:
        with (data_dir / name).open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    racks = rows("rack_plan.csv")
    for r in racks:
        for k in ("node_count", "circuits_per_side", "breaker_a", "est_weight_kg"):
            r[k] = int(r[k])
        r["planned_it_kw"] = float(r["planned_it_kw"])
    fabric = rows("fabric_plan.csv")
    for f in fabric:
        for k in ("port_count", "port_gbps", "downlinks", "uplinks"):
            f[k] = int(f[k])
    return {
        "intent": y("design_intent.yaml"),
        "facility": y("facility_envelope.yaml"),
        "storage": y("storage_plan.yaml"),
        "design": y("cluster_design.yaml"),
        "racks": racks,
        "fabric": fabric,
    }


# ----------------------------------------------------------------------------- helpers
def circuit_usable_kw(voltage_v: float, breaker_a: float, phases: int, derate: float, pf: float) -> float:
    """Usable real power of one branch circuit in kW after continuous-load derating."""
    s_va = (math.sqrt(3) if phases == 3 else 1.0) * voltage_v * breaker_a
    return s_va * derate * pf / 1000.0


def gpu_rack_max_kw(intent: dict, node_count: int) -> float:
    c = intent["compute"]
    return node_count * c["node_max_kw"] + intent["racks"]["gpu_rack_aux_kw"]


def to_gbytes_per_s(value: float, unit: str) -> float:
    """Convert a throughput quantity to GB/s (SI). Accepts 'GB/s' or 'Gb/s'."""
    if unit == "GB/s":
        return float(value)
    if unit == "Gb/s":
        return float(value) / 8.0
    raise ValueError(f"unknown unit {unit!r}")


# ----------------------------------------------------------------------------- task 1
def validate_inputs(inputs: dict[str, Any]) -> list[Finding]:
    """Return a list of findings ``{"code", "item", "message"}`` for flawed input sheets.

    Codes: DUPLICATE_RACK, POWER_BASIS, CIRCUIT_OVERLOAD, FLOOR_LOAD, PORT_OVERCOMMIT,
    OVERSUBSCRIBED_LEAF, UPLINK_MISMATCH, UNIT_MISMATCH, PSU_FEED_LOSS.
    """
    intent, fac = inputs["intent"], inputs["facility"]
    el, st = fac["electrical"], fac["structural"]
    findings: list[Finding] = []

    # Rack plan --------------------------------------------------------------
    seen: set[str] = set()
    for r in inputs["racks"]:
        rid = r["rack_id"]
        if rid in seen:
            findings.append({"code": "DUPLICATE_RACK", "item": rid,
                             "message": f"{rid} appears more than once; nodes would be double-counted"})
            continue
        seen.add(rid)
        if r["power_basis"] != "max":
            findings.append({"code": "POWER_BASIS", "item": rid,
                             "message": f"{rid} planned at {r['power_basis']} power ({r['planned_it_kw']} kW); "
                                        "electrical design must use maximum power"})
        if r["role"] == "gpu":
            load_kw = gpu_rack_max_kw(intent, r["node_count"])
        else:
            load_kw = r["planned_it_kw"]
        need_kw = load_kw * (1 + el["transient_margin"])
        usable = r["circuits_per_side"] * circuit_usable_kw(
            el["circuit_voltage_v"], r["breaker_a"], el["phases"], el["continuous_load_derate"],
            el["power_factor"])
        if need_kw > usable:
            findings.append({"code": "CIRCUIT_OVERLOAD", "item": rid,
                             "message": f"{rid} needs {need_kw:.1f} kW per side (max + transient margin) "
                                        f"but one side provides {usable:.1f} kW usable"})
        load = r["est_weight_kg"] / st["rack_footprint_m2"]
        if load > st["floor_rating_kg_per_m2"]:
            findings.append({"code": "FLOOR_LOAD", "item": rid,
                             "message": f"{rid} {load:.0f} kg/m2 exceeds rating "
                                        f"{st['floor_rating_kg_per_m2']} kg/m2"})

    # Fabric plan ------------------------------------------------------------
    target = intent["backend_fabric"]["target_oversubscription"]
    leaf_up = spine_down = 0
    for f in inputs["fabric"]:
        sid = f["switch_id"]
        if f["downlinks"] + f["uplinks"] > f["port_count"]:
            findings.append({"code": "PORT_OVERCOMMIT", "item": sid,
                             "message": f"{sid} uses {f['downlinks'] + f['uplinks']} ports of {f['port_count']}"})
        if f["tier"] == "leaf":
            leaf_up += f["uplinks"]
            ratio = f["downlinks"] / f["uplinks"] if f["uplinks"] else math.inf
            if ratio > target + 1e-9:
                findings.append({"code": "OVERSUBSCRIBED_LEAF", "item": sid,
                                 "message": f"{sid} is {ratio:.2f}:1, target {target:.2f}:1"})
        elif f["tier"] == "spine":
            spine_down += f["downlinks"]
    if leaf_up != spine_down:
        findings.append({"code": "UPLINK_MISMATCH", "item": "fabric",
                         "message": f"leaf uplinks total {leaf_up} but spine downlinks total {spine_down}"})

    # Storage plan -----------------------------------------------------------
    sto = inputs["storage"]
    for key, per in (("aggregate_read", "per_server_read_gbytes_s"),
                     ("aggregate_write", "per_server_write_gbytes_s")):
        quoted = to_gbytes_per_s(sto[key]["value"], sto[key]["unit"])
        expected = sto["servers"] * sto[per]
        if abs(quoted - expected) > 0.05 * expected:
            findings.append({"code": "UNIT_MISMATCH", "item": f"storage.{key}",
                             "message": f"{key} quoted as {sto[key]['value']} {sto[key]['unit']} "
                                        f"= {quoted:.1f} GB/s, but {sto['servers']} servers x {sto[per]} GB/s "
                                        f"= {expected:.1f} GB/s"})

    # Node PSU redundancy against loss of one feed -----------------------------
    c = intent["compute"]
    # PSU ratings are DC output, so compare with the node's DC peak load (not the AC input).
    per_feed_kw = c["psu_count"] / c["psu_feeds"] * c["psu_rating_kw"]
    if per_feed_kw < c["node_dc_peak_kw"]:
        findings.append({"code": "PSU_FEED_LOSS", "item": c["node_model"],
                         "message": f"one feed's PSUs supply {per_feed_kw:.1f} kW DC but node DC peak is "
                                    f"{c['node_dc_peak_kw']} kW; feed loss forces power braking/capping"})
    return findings


# ----------------------------------------------------------------------------- task 2
def compute_bom(intent: dict) -> dict[str, int]:
    """Bill of materials for the design intent (counts only)."""
    c, b, fe, m, rk = (intent["compute"], intent["backend_fabric"], intent["frontend_fabric"],
                       intent["management"], intent["racks"])
    nodes = c["gpu_nodes"]
    host_links = nodes * b["rails"]
    leaf_spine_links = b["rails"] * b["leaf_uplinks"]
    leaf_ports = b["rails"] * b["leaf_ports"]
    spine_ports = b["spines"] * b["spine_ports"]
    switch_ports = leaf_ports + spine_ports
    gpu_racks = math.ceil(nodes / c["nodes_per_gpu_rack"])
    backend_switches = b["rails"] + b["spines"]
    pdus = gpu_racks * m["pdus_per_gpu_rack"]
    return {
        "gpu_nodes": nodes,
        "gpus": nodes * c["gpus_per_node"],
        "gpu_racks": gpu_racks,
        "gpu_node_rack_units": nodes * c["node_rack_units"],
        "rack_units_per_gpu_rack": c["nodes_per_gpu_rack"] * c["node_rack_units"],
        "backend_leaves": b["rails"],
        "backend_spines": b["spines"],
        "backend_switches": backend_switches,
        "host_backend_links": host_links,
        "leaf_spine_links": leaf_spine_links,
        "backend_links_total": host_links + leaf_spine_links,
        "backend_switch_ports": switch_ports,
        "transceivers_single_port": 2 * (host_links + leaf_spine_links),
        "switch_side_twin_port_modules": switch_ports // 2,
        "frontend_node_ports": nodes * fe["ports_per_node"],
        "frontend_leaves": fe["leaves"],
        "gpu_rack_pdus": pdus,
        "oob_ports": nodes + backend_switches + fe["leaves"] + m["storage_servers"] + pdus,
        "total_racks": rk["gpu_racks"] + rk["network_racks"] + rk["storage_racks"] + rk["management_racks"],
    }


# ----------------------------------------------------------------------------- task 3
def compute_power_cooling(intent: dict, facility: dict) -> dict[str, float]:
    """Per-GPU-rack and cluster power, heat-removal and energy budget (all [MODELED])."""
    c, rk, eco = intent["compute"], intent["racks"], intent["economics"]
    el, co = facility["electrical"], facility["cooling"]
    n = c["nodes_per_gpu_rack"]
    rack_max = gpu_rack_max_kw(intent, n)
    rack_design = rack_max * (1 + el["transient_margin"])
    circuit_kva = math.sqrt(3) * el["circuit_voltage_v"] * 60 / 1000.0
    usable_side = 2 * circuit_usable_kw(el["circuit_voltage_v"], 60, el["phases"],
                                        el["continuous_load_derate"], el["power_factor"])
    liquid = rack_max * co["liquid_capture_fraction"]
    air = rack_max - liquid
    m_dot = liquid / (co["coolant_cp_kj_per_kg_k"] * co["design_delta_t_k"])  # kg/s
    lpm = m_dot / co["coolant_density_kg_per_l"] * 60.0
    air_m3s = air / (co["air_cp_kj_per_kg_k"] * co["air_density_kg_per_m3"] * co["air_delta_t_k"])
    all_air_m3s = rack_max / (co["air_cp_kj_per_kg_k"] * co["air_density_kg_per_m3"] * co["air_delta_t_k"])
    gpu_racks = rk["gpu_racks"]
    other_max = (rk["network_racks"] * rk["network_rack_kw"] + rk["storage_racks"] * rk["storage_rack_kw"]
                 + rk["management_racks"] * rk["management_rack_kw"])
    cluster_max = gpu_racks * rack_max + other_max
    sustained_rack = n * c["node_sustained_kw"] + rk["gpu_rack_aux_kw"]
    cluster_sustained = gpu_racks * sustained_rack + other_max
    annual_mwh = cluster_sustained * eco["pue"] * 8760 / 1000.0
    cdu_load = gpu_racks * liquid
    return {
        "rack_it_max_kw": rack_max,
        "rack_design_kw": rack_design,
        "circuit_kva": circuit_kva,
        "usable_per_side_kw": usable_side,
        "headroom_per_side_kw": usable_side - rack_design,
        "rack_liquid_kw": liquid,
        "rack_air_kw": air,
        "coolant_mass_flow_kg_s": m_dot,
        "coolant_flow_lpm": lpm,
        "rack_air_cfm": air_m3s * M3S_TO_CFM,
        "all_air_rack_cfm": all_air_m3s * M3S_TO_CFM,
        "cdu_load_kw": cdu_load,
        "cdu_utilization": cdu_load / (co["cdu_capacity_kw"] * co["cdu_count"]),
        "cluster_it_max_kw": cluster_max,
        "facility_max_kw": cluster_max * eco["pue"],
        "cluster_it_sustained_kw": cluster_sustained,
        "annual_energy_mwh": annual_mwh,
        "annual_energy_cost_usd": annual_mwh * 1000.0 * eco["energy_price_usd_per_kwh"],
    }


# ----------------------------------------------------------------------------- task 4
def compute_capacity(intent: dict, storage: dict) -> dict[str, float]:
    """Accelerator, memory, fabric, storage and utilization capacity (all [MODELED]).

    Storage aggregates are recomputed from per-server figures (the quoted aggregate
    read value in the sheet is unreliable; see validate_inputs).
    """
    c, b, w, eco = intent["compute"], intent["backend_fabric"], intent["workload"], intent["economics"]
    gpus = c["gpu_nodes"] * c["gpus_per_node"]
    injection_tbps = gpus * b["link_gbps"] / 1000.0
    leaf_ratio = b["leaf_downlinks"] / b["leaf_uplinks"]
    bisection = injection_tbps / 2.0 / max(leaf_ratio, 1.0)
    read = storage["servers"] * storage["per_server_read_gbytes_s"]
    write = storage["servers"] * storage["per_server_write_gbytes_s"]
    ckpt_gb = w["params"] * w["checkpoint_bytes_per_param"] / 1e9
    return {
        "gpus": gpus,
        "total_hbm_gb": gpus * c["gpu_hbm_gb"],
        "training_state_tb": w["params"] * w["training_bytes_per_param"] / 1e12,
        "training_state_per_gpu_gb": w["params"] * w["training_bytes_per_param"] / (w["tp"] * w["pp"]) / 1e9,
        "injection_tbps": injection_tbps,
        "bisection_tbps_per_direction": bisection,
        "leaf_oversubscription": leaf_ratio,
        "storage_read_gbytes_s": read,
        "storage_write_gbytes_s": write,
        "storage_read_per_gpu_gbytes_s": read / gpus,
        "checkpoint_gb": ckpt_gb,
        "checkpoint_write_s": ckpt_gb / write,
        "allocated_gpu_hours_per_year": gpus * 8760 * eco["allocation_target"],
    }


# ----------------------------------------------------------------------------- task 5
def failed_set(design: dict, initial: set[str]) -> set[str]:
    """Propagate failures to a fixed point. Returns the set of failed component/service ids."""
    groups = design["groups"]
    nodes = design["components"] + design["services"]
    failed = set(initial)
    changed = True
    while changed:
        changed = False
        bad_groups = {g for g, spec in groups.items()
                      if sum(m not in failed for m in spec["members"]) < spec["min_required"]}
        for comp in nodes:
            if comp["id"] not in failed and any(d in bad_groups for d in comp["depends_on"]):
                failed.add(comp["id"])
                changed = True
    return failed


def find_spofs(design: dict) -> list[dict[str, Any]]:
    """Return single points of failure as ``[{"component", "services_lost"}]`` sorted by id.

    A component is a SPOF if failing it alone (with propagation) fails any service.
    """
    services = [s["id"] for s in design["services"]]
    out = []
    for comp in design["components"]:
        failed = failed_set(design, {comp["id"]})
        lost = sorted(s for s in services if s in failed)
        if lost:
            out.append({"component": comp["id"], "services_lost": lost})
    return sorted(out, key=lambda d: d["component"])


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="ORION capacity/BOM/power model")
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
    args = parser.parse_args()
    inp = load_inputs(args.data)
    report = {
        "findings": validate_inputs(inp),
        "bom": compute_bom(inp["intent"]),
        "power_cooling": compute_power_cooling(inp["intent"], inp["facility"]),
        "capacity": compute_capacity(inp["intent"], inp["storage"]),
        "spofs": find_spofs(inp["design"]),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
