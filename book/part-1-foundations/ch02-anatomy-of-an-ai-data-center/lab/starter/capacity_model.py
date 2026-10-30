"""ORION capacity, BOM, power/cooling and failure-domain model (STARTER).

Implement every function marked TODO. Run ``python check.py`` from the lab folder to see
which checks pass. Loading helpers and small unit helpers are provided.

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
    """Usable real power of one branch circuit in kW after continuous-load derating (provided)."""
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
    # TODO: Rack plan: flag duplicate rack_id rows (DUPLICATE_RACK) and skip further checks on the duplicate.
    # TODO: Rack plan: flag power_basis != 'max' (POWER_BASIS).
    # TODO: Rack plan: per-side load = (GPU racks: node_count x node_max_kw + gpu_rack_aux_kw; others: planned_it_kw)
    # TODO:   x (1 + transient_margin); compare with circuits_per_side x circuit_usable_kw(...) (CIRCUIT_OVERLOAD).
    # TODO: Rack plan: est_weight_kg / rack_footprint_m2 > floor_rating_kg_per_m2 (FLOOR_LOAD).
    # TODO: Fabric: downlinks + uplinks > port_count (PORT_OVERCOMMIT); leaf downlinks/uplinks > target
    # TODO:   (OVERSUBSCRIBED_LEAF); sum(leaf uplinks) != sum(spine downlinks) -> item 'fabric' (UPLINK_MISMATCH).
    # TODO: Storage: convert aggregate_read/aggregate_write with to_gbytes_per_s and compare with servers x per-server
    # TODO:   figure (5 % tolerance) -> item 'storage.<key>' (UNIT_MISMATCH).
    # TODO: Node: (psu_count / psu_feeds) x psu_rating_kw (DC output) < node_dc_peak_kw (DC load) -> item = node_model (PSU_FEED_LOSS).
    # TODO: Return a list of {'code', 'item', 'message'} dicts.
    raise NotImplementedError("validate_inputs")


# ----------------------------------------------------------------------------- task 2
def compute_bom(intent: dict) -> dict[str, int]:
    """Bill of materials for the design intent (counts only)."""
    # TODO: Return the dict of counts with exactly the keys documented in lab/README.md Task 2.
    # TODO: Every link has two ends; each end needs one transceiver if all links are optical.
    raise NotImplementedError("compute_bom")


# ----------------------------------------------------------------------------- task 3
def compute_power_cooling(intent: dict, facility: dict) -> dict[str, float]:
    """Per-GPU-rack and cluster power, heat-removal and energy budget (all [MODELED])."""
    # TODO: Return the keys documented in lab/README.md Task 3. Use Q = m_dot x cp x dT for the liquid share
    # TODO:   and the air share; convert kg/s -> L/min with density, m^3/s -> CFM with M3S_TO_CFM.
    # TODO: Plan electrical capacity at MAX power plus transient margin, never at sustained power.
    raise NotImplementedError("compute_power_cooling")


# ----------------------------------------------------------------------------- task 4
def compute_capacity(intent: dict, storage: dict) -> dict[str, float]:
    """Accelerator, memory, fabric, storage and utilization capacity (all [MODELED]).

    Storage aggregates are recomputed from per-server figures (the quoted aggregate
    read value in the sheet is unreliable; see validate_inputs).
    """
    # TODO: Return the keys documented in lab/README.md Task 4.
    # TODO: Recompute storage aggregates from per-server figures; do not trust the quoted aggregates.
    raise NotImplementedError("compute_capacity")


# ----------------------------------------------------------------------------- task 5
def failed_set(design: dict, initial: set[str]) -> set[str]:
    """Propagate failures to a fixed point. Returns the set of failed component/service ids."""
    # TODO: Iterate to a fixed point: a group fails when surviving members < min_required;
    # TODO:   a component or service fails when ANY group in its depends_on has failed.
    raise NotImplementedError("failed_set")


def find_spofs(design: dict) -> list[dict[str, Any]]:
    """Return single points of failure as ``[{"component", "services_lost"}]`` sorted by id.

    A component is a SPOF if failing it alone (with propagation) fails any service.
    """
    # TODO: For every component (not services) fail it alone, propagate with failed_set, and record which
    # TODO:   services were lost. Return [{'component': id, 'services_lost': sorted list}] sorted by component.
    raise NotImplementedError("find_spofs")


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
