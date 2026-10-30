#!/usr/bin/env python3
"""Generate the Chapter 2 lab input sheets for the ORION capacity/BOM/power model.

The sheets mimic what a build team receives from several sources: a design-intent
sheet, a rack plan from the deployment planner, a fabric plan from the network team,
a storage sizing sheet from a vendor, a facility envelope from the MEP engineer, and a
dependency model used for failure-domain analysis. Some sheets contain deliberate
errors; they are documented only in the instructor solutions. This generator is instructor
material and is stripped from the student release.

All values are [ILLUSTRATIVE] and derived from docs/REFERENCE_CLUSTER.md (ORION-256).

Usage:
    python tools/generate_inputs.py                 # writes ../data/
    python tools/generate_inputs.py --out some/dir  # writes elsewhere (for byte-compare)
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import yaml

SEED = 2


def design_intent() -> dict:
    """Design intent for ORION-256. Units are in the key names."""
    return {
        "cluster": "ORION-256",
        "evidence_class": "ILLUSTRATIVE",
        "compute": {
            "gpu_nodes": 32,
            "gpus_per_node": 8,
            "node_model": "HX8",
            "node_rack_units": 8,
            "nodes_per_gpu_rack": 4,
            "gpu_hbm_gb": 80,
            "node_max_kw": 10.2,
            "node_dc_peak_kw": 9.59,
            "node_sustained_kw": 8.5,
            "psu_count": 6,
            "psu_rating_kw": 3.0,
            "psu_feeds": 2,
        },
        "backend_fabric": {
            "rails": 8,
            "link_gbps": 400,
            "leaf_ports": 64,
            "leaf_downlinks": 32,
            "leaf_uplinks": 32,
            "spines": 4,
            "spine_ports": 64,
            "target_oversubscription": 1.0,
        },
        "frontend_fabric": {
            "ports_per_node": 2,
            "port_gbps": 200,
            "leaves": 2,
            "oversubscription_by_ports": 3.0,
            "oversubscription_by_bandwidth": 1.5,
        },
        "management": {
            "pdus_per_gpu_rack": 4,
            "storage_servers": 8,
        },
        "racks": {
            "gpu_racks": 8,
            "network_racks": 2,
            "storage_racks": 2,
            "management_racks": 1,
            "gpu_rack_aux_kw": 0.2,
            "network_rack_kw": 16.0,
            "storage_rack_kw": 9.0,
            "management_rack_kw": 4.0,
        },
        "workload": {
            "params": 70_000_000_000,
            "training_bytes_per_param": 16,
            "checkpoint_bytes_per_param": 14,
            "tp": 8,
            "pp": 4,
            "dp": 8,
        },
        "economics": {
            "pue": 1.25,
            "energy_price_usd_per_kwh": 0.08,
            "allocation_target": 0.85,
        },
    }


def facility_envelope() -> dict:
    """Facility envelope as supplied by the MEP engineer of record."""
    return {
        "evidence_class": "ILLUSTRATIVE",
        "electrical": {
            "circuit_voltage_v": 415,
            "phases": 3,
            "continuous_load_derate": 0.80,
            "power_factor": 0.95,
            "transient_margin": 0.10,
        },
        "cooling": {
            "method": "direct_to_chip_plus_air",
            "liquid_capture_fraction": 0.75,
            "coolant": "PG25",
            "coolant_cp_kj_per_kg_k": 3.90,
            "coolant_density_kg_per_l": 1.02,
            "tcs_supply_c": 30,
            "design_delta_t_k": 10,
            "air_cp_kj_per_kg_k": 1.006,
            "air_density_kg_per_m3": 1.20,
            "air_delta_t_k": 15,
            "cdu_count": 1,
            "cdu_capacity_kw": 300,
        },
        "structural": {
            "rack_footprint_m2": 0.72,
            "floor_rating_kg_per_m2": 1200,
        },
    }


def rack_plan(rng: random.Random) -> list[dict]:
    rows: list[dict] = []
    for i in range(1, 9):
        rows.append({
            "rack_id": f"rack-{i:02d}",
            "role": "gpu",
            "node_count": 4,
            "power_basis": "max",
            "planned_it_kw": 41.0,
            "circuits_per_side": 2,
            "breaker_a": 60,
            "est_weight_kg": 820 + rng.randint(-20, 20),
        })
    # Planted flaws (documented in solutions/ only).
    rows[2]["power_basis"] = "sustained"
    rows[2]["planned_it_kw"] = 34.2
    rows[6]["circuits_per_side"] = 1
    rows[7]["est_weight_kg"] = 1000
    rows.insert(5, dict(rows[4]))  # duplicate of rack-05
    for rid, kw in (("NET-1", 16.0), ("NET-2", 16.0)):
        rows.append({"rack_id": rid, "role": "network", "node_count": 0, "power_basis": "max",
                     "planned_it_kw": kw, "circuits_per_side": 1, "breaker_a": 60,
                     "est_weight_kg": 520 + rng.randint(-20, 20)})
    for rid in ("STO-1", "STO-2"):
        rows.append({"rack_id": rid, "role": "storage", "node_count": 0, "power_basis": "max",
                     "planned_it_kw": 9.0, "circuits_per_side": 1, "breaker_a": 32,
                     "est_weight_kg": 610 + rng.randint(-20, 20)})
    rows.append({"rack_id": "MGMT-1", "role": "management", "node_count": 0, "power_basis": "max",
                 "planned_it_kw": 4.0, "circuits_per_side": 1, "breaker_a": 32,
                 "est_weight_kg": 380 + rng.randint(-20, 20)})
    return rows


def fabric_plan() -> list[dict]:
    rows = []
    for r in range(8):
        rows.append({"switch_id": f"orion-be-leaf-r{r}", "tier": "leaf", "rail": r, "port_count": 64,
                     "port_gbps": 400, "downlinks": 32, "uplinks": 32})
    rows[5]["uplinks"] = 24
    for s in range(1, 5):
        rows.append({"switch_id": f"orion-be-spine-{s}", "tier": "spine", "rail": "", "port_count": 64,
                     "port_gbps": 400, "downlinks": 64, "uplinks": 0})
    rows[9]["downlinks"] = 72
    return rows


def storage_plan() -> dict:
    return {
        "evidence_class": "ILLUSTRATIVE",
        "source": "storage vendor sizing sheet",
        "servers": 8,
        "per_server_read_gbytes_s": 20.0,
        "per_server_write_gbytes_s": 10.0,
        "aggregate_read": {"value": 160, "unit": "Gb/s"},
        "aggregate_write": {"value": 80, "unit": "GB/s"},
    }


def cluster_design() -> dict:
    """Dependency model for failure-domain analysis.

    A component fails if ANY group in its ``depends_on`` list has fewer surviving
    members than ``min_required``. Services are the things the business cares about.
    """
    groups: dict[str, dict] = {
        "utility-or-generator": {"members": ["utility-1", "generator-1"], "min_required": 1},
        "ups-a": {"members": ["ups-A"], "min_required": 1},
        "ups-b": {"members": ["ups-B"], "min_required": 1},
        "busway-a": {"members": ["busway-A"], "min_required": 1},
        "busway-b": {"members": ["busway-B"], "min_required": 1},
        "chillers": {"members": ["chiller-1", "chiller-2", "chiller-3"], "min_required": 2},
        "gpu-row-cooling": {"members": ["cdu-1"], "min_required": 1},
        "net-power": {"members": ["pdu-net-A", "pdu-net-B"], "min_required": 1},
        "fe-leaf-power": {"members": ["pdu-net-A"], "min_required": 1},
        "frontend-leaves": {"members": ["fe-leaf-1", "fe-leaf-2"], "min_required": 1},
        "border-routers": {"members": ["border-1", "border-2"], "min_required": 1},
        "backend-spines": {"members": [f"orion-be-spine-{s}" for s in range(1, 5)], "min_required": 3},
        "backend-rails": {"members": [f"orion-be-leaf-r{r}" for r in range(8)], "min_required": 8},
        "oob-mgmt": {"members": ["oob-sw-1"], "min_required": 1},
        "storage-data": {"members": [f"stor-{i:02d}" for i in range(1, 9)], "min_required": 7},
        "storage-metadata": {"members": ["mds-1"], "min_required": 1},
        "slurm-controller": {"members": ["slurmctld-1"], "min_required": 1},
        "k8s-control-plane": {"members": ["k8s-cp-1", "k8s-cp-2", "k8s-cp-3"], "min_required": 2},
        "gpu-nodes": {"members": [f"orion-n{n + 1:02d}" for n in range(32)], "min_required": 28},
        "storage-power": {"members": ["pdu-sto-A", "pdu-sto-B"], "min_required": 1},
        "mgmt-power": {"members": ["pdu-mgmt-A", "pdu-mgmt-B"], "min_required": 1},
    }
    comps: list[dict] = []

    def add(cid: str, ctype: str, deps: list[str]) -> None:
        comps.append({"id": cid, "type": ctype, "depends_on": deps})

    add("utility-1", "utility", [])
    add("generator-1", "generator", [])
    add("ups-A", "ups", ["utility-or-generator"])
    add("ups-B", "ups", ["utility-or-generator"])
    add("busway-A", "busway", ["ups-a"])
    add("busway-B", "busway", ["ups-b"])
    for c in ("chiller-1", "chiller-2", "chiller-3"):
        add(c, "chiller", ["utility-or-generator"])
    add("cdu-1", "cdu", ["chillers", "utility-or-generator"])
    for r in range(1, 9):
        groups[f"rack-{r:02d}-power"] = {"members": [f"pdu-rack-{r:02d}-A", f"pdu-rack-{r:02d}-B"], "min_required": 1}
        add(f"pdu-rack-{r:02d}-A", "rack-pdu", ["busway-a"])
        add(f"pdu-rack-{r:02d}-B", "rack-pdu", ["busway-b"])
    for side, bus in (("A", "busway-a"), ("B", "busway-b")):
        add(f"pdu-net-{side}", "rack-pdu", [bus])
        add(f"pdu-sto-{side}", "rack-pdu", [bus])
        add(f"pdu-mgmt-{side}", "rack-pdu", [bus])
    for n in range(32):
        rack = n // 4 + 1
        add(f"orion-n{n + 1:02d}", "gpu-node", [f"rack-{rack:02d}-power", "gpu-row-cooling"])
    for r in range(8):
        add(f"orion-be-leaf-r{r}", "rail-leaf", ["net-power"])
    for s in range(1, 5):
        add(f"orion-be-spine-{s}", "spine", ["net-power"])
    add("fe-leaf-1", "frontend-leaf", ["fe-leaf-power"])
    add("fe-leaf-2", "frontend-leaf", ["fe-leaf-power"])
    add("border-1", "border-router", ["net-power"])
    add("border-2", "border-router", ["net-power"])
    add("oob-sw-1", "oob-switch", ["mgmt-power"])
    for i in range(1, 9):
        add(f"stor-{i:02d}", "storage-server", ["storage-power", "frontend-leaves"])
    add("mds-1", "metadata-server", ["storage-power", "frontend-leaves"])
    add("slurmctld-1", "scheduler", ["mgmt-power", "frontend-leaves"])
    for i in range(1, 4):
        add(f"k8s-cp-{i}", "k8s-control-plane", ["mgmt-power", "frontend-leaves"])
    services = [
        {"id": "svc-training", "type": "service",
         "depends_on": ["gpu-nodes", "backend-spines", "backend-rails", "storage-data",
                        "storage-metadata", "slurm-controller", "frontend-leaves"]},
        {"id": "svc-inference", "type": "service",
         "depends_on": ["gpu-nodes", "frontend-leaves", "border-routers", "k8s-control-plane"]},
        {"id": "svc-management", "type": "service", "depends_on": ["oob-mgmt"]},
    ]
    return {"evidence_class": "ILLUSTRATIVE", "groups": dict(sorted(groups.items())),
            "components": comps, "services": services}


def write_yaml(path: Path, obj: dict) -> None:
    path.write_text(yaml.safe_dump(obj, sort_keys=False, default_flow_style=False), encoding="utf-8",
                    newline="\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def generate(out: Path, seed: int = SEED) -> None:
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    write_yaml(out / "design_intent.yaml", design_intent())
    write_yaml(out / "facility_envelope.yaml", facility_envelope())
    write_csv(out / "rack_plan.csv", rack_plan(rng))
    write_csv(out / "fabric_plan.csv", fabric_plan())
    write_yaml(out / "storage_plan.yaml", storage_plan())
    write_yaml(out / "cluster_design.yaml", cluster_design())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    generate(args.out, args.seed)
    print(f"wrote inputs to {args.out}")


if __name__ == "__main__":
    main()
