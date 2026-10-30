"""Chapter 21 lab - capacity forecast, TCO, design comparison, and power-capping trade-off.

STARTER: implement every function that raises NotImplementedError (helpers and the loader are
given). Reference API mirrors solutions/lab/capacity_model.py.

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
    # TODO: drop_duplicates() removes identical rows; then any remaining duplicated quarter is a conflict -> ValueError.
    raise NotImplementedError("clean_plan")


# --------------------------------------------------------------------------- Task 2: forecast
def usable_fraction(a: dict[str, Any]) -> float:
    """(1 - maintenance) x (1 - failure_repair) x (1 - fragmentation)."""
    # TODO: Multiply the three (1 - reserve) factors from a['reserves'].
    raise NotImplementedError("usable_fraction")


def it_kw_per_gpu(a: dict[str, Any]) -> float:
    """Provisioned IT kW per GPU including network/storage overhead."""
    # TODO: provisioned node kW x (1 + network_storage_overhead) / gpus_per_node.
    raise NotImplementedError("it_kw_per_gpu")


def forecast(plan: pd.DataFrame, a: dict[str, Any]) -> pd.DataFrame:
    """Quarterly capacity table. Columns:
    quarter, installed (cumulative nominal GPUs), energizable (floor(facility_kw / it_kw_per_gpu) rounded
    down to whole nodes), energized = min(installed, energizable), stranded = installed - energized,
    usable = energized x usable_fraction, demand = train + infer GPUs, required = demand / target_allocation,
    gap = usable - required, status = 'OK' | 'SHORTFALL'."""
    # TODO: Iterate the cleaned plan; keep a running installed count; energizable is facility kW / kW-per-GPU rounded DOWN to whole nodes.
    raise NotImplementedError("forecast")


def first_shortfall(fc: pd.DataFrame) -> str | None:
    # TODO: First quarter whose status is SHORTFALL, else None.
    raise NotImplementedError("first_shortfall")


def order_deadlines(quarter: str, a: dict[str, Any]) -> dict[str, str]:
    """Latest quarter by which each resource must be ordered to be in service by `quarter`."""
    # TODO: Use quarter_add(quarter, -lead) for each entry of a['lead_time_quarters'].
    raise NotImplementedError("order_deadlines")


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
    # TODO: Follow the docstring formulas exactly; hardware capex (incl. fixed) feeds both amortization and support.
    raise NotImplementedError("tco")


# --------------------------------------------------------------------------- Task 4: design comparison
def compare_designs(dz: dict[str, Any], a: dict[str, Any]) -> pd.DataFrame:
    """For each design: nodes that fit the hall = min(floor(facility_it_kw / (provisioned kW x (1+overhead))),
    floor(liquid_cooling_kw_available / (provisioned kW x liquid_fraction)) if liquid_fraction > 0);
    gpus; useful throughput = nodes x gpus_per_node x rel_throughput_per_gpu x comm_efficiency x
    usable_fraction x target_allocation x goodput (units: HX8-GPU equivalents of useful work);
    annual TCO (tco(), staff scaled by nodes/32); throughput per $M/year; throughput per facility MW
    (sustained IT x (1+overhead) x PUE); usd per nominal GPU per year; usd per useful unit per year."""
    # TODO: Nodes are limited by facility IT kW and, for liquid-cooled designs, by CDU capacity; reuse tco().
    raise NotImplementedError("compare_designs")


# --------------------------------------------------------------------------- Task 5: power capping
def power_cap_tradeoff(curve: pd.DataFrame, c: dict[str, Any]) -> pd.DataFrame:
    """Per cap: node_peak_kw = base + gpus x cap/1000; nodes_per_rack = min(slots,
    floor(rack_limit x (1 - margin) / node_peak)); deployable = min(nodes, racks x nodes_per_rack);
    cluster_throughput = deployable x rel_throughput (node-equivalents); racks_needed_for_all =
    ceil(nodes / nodes_per_rack); throughput_per_kw = rel_throughput / node_peak_kw;
    unused_budget_kw = rack budget - nodes_per_rack x node_peak (planned power left stranded per rack).
    Sorted by cap ascending."""
    # TODO: Planned peak per rack must stay <= rack_limit x (1 - transient_margin); slots cap nodes per rack.
    raise NotImplementedError("power_cap_tradeoff")


def best_cap(table: pd.DataFrame) -> int:
    """Cap with the highest cluster_throughput; ties go to the higher cap."""
    # TODO: Sort by cluster_throughput desc, then cap desc.
    raise NotImplementedError("best_cap")


# --------------------------------------------------------------------------- Task 6: misleading nominal counts
def misleading_nominal_flags(fc: pd.DataFrame, cmp: pd.DataFrame) -> dict[str, list[str]]:
    """Flags where nominal GPU count misleads:
    STRANDED_GPUS: quarters with stranded > 0 (installed but not energizable)
    RESERVE_SHORTFALL: quarters where installed GPUs alone would exceed `required` but status is SHORTFALL
    PER_GPU_COST_MISLEADS: designs whose usd_per_gpu_year is higher than another design's while their
                           usd_per_useful_unit_year is lower
    Returns {flag: [quarters or design names]} (only non-empty flags)."""
    # TODO: Compare installed with required (nominal view) against status (usable view); compare per-GPU and per-useful-unit costs pairwise.
    raise NotImplementedError("misleading_nominal_flags")
