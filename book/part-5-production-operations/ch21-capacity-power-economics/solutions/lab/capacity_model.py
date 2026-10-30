"""Chapter 21 lab - capacity forecast, TCO, design comparison, and power-capping trade-off.

REFERENCE SOLUTION (instructors). Same public API as lab/starter/capacity_model.py.

Units: GPUs (count), kW (IT unless stated), USD, GPU-hours. All outputs are [MODELED].
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

HOURS_PER_YEAR = 8760


# --------------------------------------------------------------------------- loading (given)
def load_inputs(data_dir: Path) -> dict[str, Any]:
    """Load all lab inputs. Provided complete in the starter."""
    d = Path(data_dir)
    return {
        "plan": pd.read_csv(d / "quarterly_plan.csv", keep_default_na=False),
        "assumptions": yaml.safe_load((d / "assumptions.yaml").read_text(encoding="utf-8")),
        "designs": yaml.safe_load((d / "designs.yaml").read_text(encoding="utf-8")),
        "curve": pd.read_csv(d / "power_cap_curve.csv"),
        "cap_case": yaml.safe_load((d / "power_cap_case.yaml").read_text(encoding="utf-8")),
    }


def quarter_add(q: str, n: int) -> str:
    """'2028Q2' + (-2) -> '2027Q4'. Given helper."""
    y, k = int(q[:4]), int(q[5])
    idx = y * 4 + (k - 1) + n
    return f"{idx // 4}Q{idx % 4 + 1}"


# --------------------------------------------------------------------------- Task 1: data hygiene
def clean_plan(plan: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows, then raise ValueError if any quarter still appears more than once
    (conflicting duplicates need a human). Return sorted by quarter with a fresh index."""
    p = plan.drop_duplicates()
    dup = p.quarter[p.quarter.duplicated()]
    if not dup.empty:
        raise ValueError(f"conflicting rows for {sorted(set(dup))}")
    return p.sort_values("quarter").reset_index(drop=True)


# --------------------------------------------------------------------------- Task 2: forecast
def usable_fraction(a: dict[str, Any]) -> float:
    """(1 - maintenance) x (1 - failure_repair) x (1 - fragmentation)."""
    r = a["reserves"]
    return (1 - r["maintenance"]) * (1 - r["failure_repair"]) * (1 - r["fragmentation"])


def it_kw_per_gpu(a: dict[str, Any]) -> float:
    """Provisioned IT kW per GPU including network/storage overhead."""
    return a["provisioned_it_kw_per_node"] * (1 + a["network_storage_overhead"]) / a["gpus_per_node"]


def forecast(plan: pd.DataFrame, a: dict[str, Any]) -> pd.DataFrame:
    """Quarterly capacity table. Columns:
    quarter, installed (cumulative nominal GPUs), energizable (floor(facility_kw / it_kw_per_gpu) rounded
    down to whole nodes), energized = min(installed, energizable), stranded = installed - energized,
    usable = energized x usable_fraction, demand = train + infer GPUs, required = demand / target_allocation,
    gap = usable - required, status = 'OK' | 'SHORTFALL'."""
    p = clean_plan(plan)
    g = a["gpus_per_node"]
    installed = a["initial_installed_gpus"]
    rows = []
    for r in p.itertuples():
        installed += int(r.gpus_delivered) - int(r.gpus_decommissioned)
        energizable = int(math.floor(r.facility_it_kw / it_kw_per_gpu(a) / g)) * g
        energized = min(installed, energizable)
        usable = energized * usable_fraction(a)
        demand = int(r.demand_train_gpus) + int(r.demand_infer_gpus)
        required = demand / a["target_allocation"]
        rows.append((r.quarter, installed, energizable, energized, installed - energized, round(usable, 1),
                     demand, round(required, 1), round(usable - required, 1),
                     "OK" if usable >= required else "SHORTFALL"))
    return pd.DataFrame(rows, columns=["quarter", "installed", "energizable", "energized", "stranded", "usable",
                                       "demand", "required", "gap", "status"])


def first_shortfall(fc: pd.DataFrame) -> str | None:
    s = fc[fc.status == "SHORTFALL"]
    return None if s.empty else str(s.quarter.iloc[0])


def order_deadlines(quarter: str, a: dict[str, Any]) -> dict[str, str]:
    """Latest quarter by which each resource must be ordered to be in service by `quarter`."""
    return {k: quarter_add(quarter, -v) for k, v in a["lead_time_quarters"].items()}


# --------------------------------------------------------------------------- Task 3: TCO
def tco(nodes: int, d: dict[str, Any], a: dict[str, Any], staff_usd: float | None = None,
        fixed_capex_usd: float = 0.0) -> dict[str, float]:
    """Annual TCO for `nodes` nodes of design-like dict `d` (keys: gpus_per_node, node_capex_usd,
    network_capex_per_node_usd, cooling_capex_per_node_usd (optional), provisioned_it_kw_per_node,
    sustained_it_kw_per_node, pue (optional, else a.prices.pue)).

    capex_per_year  = (nodes x (node + network + cooling capex) + fixed_capex) / amortization_years
    power_per_year  = nodes x sustained kW x (1 + overhead) x PUE x 8760 x $/kWh
    space_per_year  = nodes x provisioned kW x (1 + overhead) x colo $/kW-month x 12
    support         = support_fraction x hardware capex
    staff           = staff_usd (default a.prices.staff_usd_per_year scaled by nodes / 32)
    Returns the components, total, and cost per nominal, allocated, and useful GPU-hour where
    allocated = nominal x usable_fraction x target_allocation and useful = allocated x goodput."""
    pr = a["prices"]
    ov = a["network_storage_overhead"]
    pue = d.get("pue", pr["pue"])
    hw = nodes * (d["node_capex_usd"] + d["network_capex_per_node_usd"] + d.get("cooling_capex_per_node_usd", 0)) \
        + fixed_capex_usd
    capex = hw / pr["amortization_years"]
    power = nodes * d["sustained_it_kw_per_node"] * (1 + ov) * pue * HOURS_PER_YEAR * pr["electricity_usd_per_kwh"]
    space = nodes * d["provisioned_it_kw_per_node"] * (1 + ov) * pr["colo_usd_per_kw_month"] * 12
    support = pr["support_fraction_of_hw_capex"] * hw
    staff = pr["staff_usd_per_year"] * nodes / 32 if staff_usd is None else staff_usd
    total = capex + power + space + support + staff
    nominal = nodes * d["gpus_per_node"] * HOURS_PER_YEAR
    allocated = nominal * usable_fraction(a) * a["target_allocation"]
    useful = allocated * a["goodput"]
    return {"capex": capex, "power": power, "space": space, "support": support, "staff": staff, "total": total,
            "usd_per_nominal_gpu_h": total / nominal, "usd_per_allocated_gpu_h": total / allocated,
            "usd_per_useful_gpu_h": total / useful}


# --------------------------------------------------------------------------- Task 4: design comparison
def compare_designs(dz: dict[str, Any], a: dict[str, Any]) -> pd.DataFrame:
    """For each design: nodes that fit the hall = min(floor(facility_it_kw / (provisioned kW x (1+overhead))),
    floor(liquid_cooling_kw_available / (provisioned kW x liquid_fraction)) if liquid_fraction > 0);
    gpus; useful throughput = nodes x gpus_per_node x rel_throughput_per_gpu x comm_efficiency x
    usable_fraction x target_allocation x goodput (units: HX8-GPU equivalents of useful work);
    annual TCO (tco(), staff scaled by nodes/32); throughput per $M/year; throughput per facility MW
    (sustained IT x (1+overhead) x PUE); usd per nominal GPU per year; usd per useful unit per year."""
    ov = a["network_storage_overhead"]
    rows = []
    for d in dz["designs"]:
        per_node_kw = d["provisioned_it_kw_per_node"] * (1 + ov)
        n = int(dz["facility_it_kw"] // per_node_kw)
        if d["liquid_fraction"] > 0:
            n = min(n, int(dz["liquid_cooling_kw_available"] // (d["provisioned_it_kw_per_node"] * d["liquid_fraction"])))
        useful = n * d["gpus_per_node"] * d["rel_throughput_per_gpu"] * d["comm_efficiency"] * usable_fraction(a) \
            * a["target_allocation"] * a["goodput"]
        t = tco(n, d, a)
        fac_mw = n * d["sustained_it_kw_per_node"] * (1 + ov) * d["pue"] / 1000
        gpus = n * d["gpus_per_node"]
        rows.append((d["name"], n, gpus, round(useful, 1), round(t["total"]), round(useful / (t["total"] / 1e6), 2),
                     round(useful / fac_mw, 1), round(t["total"] / gpus), round(t["total"] / useful)))
    return pd.DataFrame(rows, columns=["design", "nodes", "gpus", "useful_units", "tco_usd_per_year",
                                       "useful_per_musd", "useful_per_facility_mw", "usd_per_gpu_year",
                                       "usd_per_useful_unit_year"])


# --------------------------------------------------------------------------- Task 5: power capping
def power_cap_tradeoff(curve: pd.DataFrame, c: dict[str, Any]) -> pd.DataFrame:
    """Per cap: node_peak_kw = base + gpus x cap/1000; nodes_per_rack = min(slots,
    floor(rack_limit x (1 - margin) / node_peak)); deployable = min(nodes, racks x nodes_per_rack);
    cluster_throughput = deployable x rel_throughput (node-equivalents); racks_needed_for_all =
    ceil(nodes / nodes_per_rack); throughput_per_kw = rel_throughput / node_peak_kw;
    unused_budget_kw = rack budget - nodes_per_rack x node_peak (planned power left stranded per rack).
    Sorted by cap ascending."""
    rows = []
    budget = c["rack_limit_kw"] * (1 - c["transient_margin"])
    for r in curve.sort_values("gpu_power_cap_w").itertuples():
        peak = c["node_base_peak_kw"] + c["gpus_per_node"] * r.gpu_power_cap_w / 1000
        npr = min(c["rack_slots"], int(budget // peak))
        dep = min(c["nodes"], c["racks"] * npr)
        rows.append((int(r.gpu_power_cap_w), round(peak, 2), npr, dep, round(dep * r.rel_throughput, 2),
                     math.ceil(c["nodes"] / npr) if npr else None, round(r.rel_throughput / peak, 4),
                     round(budget - npr * peak, 2)))
    return pd.DataFrame(rows, columns=["cap_w", "node_peak_kw", "nodes_per_rack", "deployable_nodes",
                                       "cluster_throughput", "racks_needed_for_all", "throughput_per_kw",
                                       "unused_budget_kw"])


def best_cap(table: pd.DataFrame) -> int:
    """Cap with the highest cluster_throughput; ties go to the higher cap."""
    t = table.sort_values(["cluster_throughput", "cap_w"], ascending=[False, False])
    return int(t.cap_w.iloc[0])


# --------------------------------------------------------------------------- Task 6: misleading nominal counts
def misleading_nominal_flags(fc: pd.DataFrame, cmp: pd.DataFrame) -> dict[str, list[str]]:
    """Flags where nominal GPU count misleads:
    STRANDED_GPUS: quarters with stranded > 0 (installed but not energizable)
    RESERVE_SHORTFALL: quarters where installed GPUs alone would exceed `required` but status is SHORTFALL
    PER_GPU_COST_MISLEADS: designs whose usd_per_gpu_year is higher than another design's while their
                           usd_per_useful_unit_year is lower
    Returns {flag: [quarters or design names]} (only non-empty flags)."""
    out: dict[str, list[str]] = {}
    s = list(fc[fc.stranded > 0].quarter)
    if s:
        out["STRANDED_GPUS"] = s
    r = list(fc[(fc.installed >= fc.required) & (fc.status == "SHORTFALL")].quarter)
    if r:
        out["RESERVE_SHORTFALL"] = r
    m = []
    for x in cmp.itertuples():
        for y in cmp.itertuples():
            if x.usd_per_gpu_year > y.usd_per_gpu_year and x.usd_per_useful_unit_year < y.usd_per_useful_unit_year:
                m.append(x.design)
    if m:
        out["PER_GPU_COST_MISLEADS"] = sorted(set(m))
    return out
