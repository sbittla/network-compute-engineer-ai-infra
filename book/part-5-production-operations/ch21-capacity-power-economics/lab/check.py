#!/usr/bin/env python3
"""Checker for the Chapter 21 lab (capacity forecast, TCO, design comparison, power capping).

Usage:
    python check.py                    # check your starter/ implementation (default)
    python check.py --impl solution    # check the reference implementation (instructors)

Prints one line per check (PASS / FAIL / TODO) and exits 0 only if every check passes.
Pure Python, no hardware, no network, < 60 s.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FILES = ("quarterly_plan.csv", "assumptions.yaml", "designs.yaml", "power_cap_curve.csv", "power_cap_case.yaml")
ORION = {"gpus_per_node": 8, "node_capex_usd": 320000, "network_capex_per_node_usd": 85000,
         "provisioned_it_kw_per_node": 10.2, "sustained_it_kw_per_node": 8.5}


def load_impl(impl: str) -> ModuleType:
    path = HERE / "starter" / "capacity_model.py" if impl == "starter" else \
        HERE.parent / "solutions" / "lab" / "capacity_model.py"
    spec = importlib.util.spec_from_file_location(f"capacity_model_{impl}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def close(x: float, y: float, rel: float = 0.005) -> bool:
    return math.isclose(x, y, rel_tol=rel)


def hint(msg: str, hints: list[str]) -> str:
    """Append diagnostic hints (common mistakes recognized from the wrong values) to a FAIL message."""
    sep = "\n      hint: "
    return msg + ("" if not hints else sep + sep.join(hints))


class Ctx:
    def __init__(self, m: ModuleType) -> None:
        self.m = m
        self.b: dict[str, Any] = m.load_inputs(DATA)
        self.a = self.b["assumptions"]


def check_reproducible(c: Ctx) -> tuple[bool | None, str]:
    if not (HERE / "tools" / "generate_data.py").exists():
        return None, "generator not shipped (instructor copy only); data integrity not re-checked"
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([sys.executable, str(HERE / "tools" / "generate_data.py"), "--out", td],
                       check=True, capture_output=True)
        for n in FILES:
            if (DATA / n).read_bytes() != (Path(td) / n).read_bytes():
                return False, f"{n} differs from regenerated copy"
    digest = hashlib.sha256(b"".join((DATA / n).read_bytes() for n in FILES)).hexdigest()[:12]
    return True, f"generator reproduces committed data byte-for-byte (sha256 {digest})"


def check_clean(c: Ctx) -> tuple[bool, str]:
    p = c.m.clean_plan(c.b["plan"])
    bad = c.b["plan"].copy()
    bad.loc[len(bad)] = ["2027Q4", 0, 0, 800, 999, 1, "conflict"]
    try:
        c.m.clean_plan(bad)
        raised = False
    except ValueError:
        raised = True
    ok = len(p) == 12 and p.quarter.is_unique and raised
    return ok, f"{len(p)} quarters after removing the exact duplicate; conflicting duplicate raises={raised}"


def check_fractions(c: Ctx) -> tuple[bool, str]:
    u, k = c.m.usable_fraction(c.a), c.m.it_kw_per_gpu(c.a)
    return close(u, 0.849623) and close(k, 1.428), f"usable fraction={u:.4f} (expect 0.8496); IT kW/GPU={k:.3f} (expect 1.428)"


def check_forecast(c: Ctx) -> tuple[bool, str]:
    fc = c.m.forecast(c.b["plan"], c.a)
    r = fc.set_index("quarter")
    ok = (int(r.loc["2028Q2", "energized"]) == 560 and int(r.loc["2028Q2", "stranded"]) == 464
          and close(float(r.loc["2028Q3", "usable"]), 475.8, 0.002) and close(float(r.loc["2028Q3", "required"]), 494.1, 0.002)
          and r.loc["2028Q3", "status"] == "SHORTFALL" and int(r.loc["2029Q3", "installed"]) == 1024
          and r.loc["2029Q4", "status"] == "SHORTFALL")
    msg = (f"2028Q2 energized/stranded={r.loc['2028Q2', 'energized']}/{r.loc['2028Q2', 'stranded']}; "
           f"2028Q3 usable {r.loc['2028Q3', 'usable']} vs required {r.loc['2028Q3', 'required']} -> {r.loc['2028Q3', 'status']}")
    hints = []
    if not ok:
        if fc.quarter.duplicated().any() or 768 in set(fc.loc[fc.quarter == "2027Q3", "installed"].astype(int)):
            hints.append("2027Q3 installed is 768, not 512: the exact duplicate 2027Q3 row was counted (call clean_plan first)")
        if close(float(r.loc["2028Q3", "usable"]), 1024 * 0.849623, 0.002):
            hints.append("2028Q3 usable is computed from installed GPUs: use energized = min(installed, energizable)")
        if close(float(r.loc["2028Q3", "required"]), 420, 0.002):
            hints.append("required equals demand: divide by target_allocation (0.85) for queueing headroom")
        if int(r.loc["2028Q2", "energizable"]) % 8:
            hints.append("energizable GPUs must be rounded down to whole 8-GPU nodes")
    return ok, hint(msg, hints)


def check_shortfall(c: Ctx) -> tuple[bool, str]:
    fc = c.m.forecast(c.b["plan"], c.a)
    q = c.m.first_shortfall(fc)
    d = c.m.order_deadlines(q, c.a)
    ok = q == "2028Q3" and d == {"gpus": "2028Q1", "network": "2028Q2", "facility_power": "2027Q3"}
    hints = []
    if q != "2028Q3":
        hints.append("the first shortfall is power-caused (2028Q3: 1,024 installed, 560 energized); compare usable with required")
    elif d.get("facility_power") == "2028Q3" or d.get("gpus") == "2028Q3":
        hints.append("order-by = shortfall quarter - lead time - onboarding (quarter_add with a negative count)")
    return ok, hint(f"first shortfall={q}; order-by={d}", hints)


def check_tco(c: Ctx) -> tuple[bool, str]:
    t = c.m.tco(32, ORION, c.a, fixed_capex_usd=2_000_000)
    ok = (close(t["total"], 6_733_951, 0.001) and close(t["usd_per_nominal_gpu_h"], 3.003, 0.002)
          and close(t["usd_per_allocated_gpu_h"], 4.158, 0.002) and close(t["usd_per_useful_gpu_h"], 4.725, 0.002))
    msg = (f"ORION-256 TCO ${t['total']/1e6:.2f}M/yr; $/GPU-h nominal {t['usd_per_nominal_gpu_h']:.2f}, "
           f"allocated {t['usd_per_allocated_gpu_h']:.2f}, useful {t['usd_per_useful_gpu_h']:.2f} (expect 3.00/4.16/4.72)")
    hints = []
    if not ok:
        if close(t["total"], 6_733_951 - 2_000_000 * (1 / 4 + 0.08), 0.002):
            hints.append("total is $0.66M low: add fixed_capex_usd (storage) to both amortized capex and support")
        if close(t["total"], 6_733_951 - 304.64 * 0.25 * 8760 * 0.08, 0.002):
            hints.append("power cost is missing PUE (facility kW = IT kW x 1.25)")
        if close(t["usd_per_allocated_gpu_h"], 3.003 / 0.85, 0.003):
            hints.append("allocated $/GPU-h divides by allocation only: divide by usable fraction x allocation")
    return ok, hint(msg, hints)


def check_designs(c: Ctx) -> tuple[bool, str]:
    d = c.m.compare_designs(c.b["designs"], c.a).set_index("design")
    A, B = d.loc["A-air-H100class"], d.loc["B-liquid-nextgen"]
    ok = (int(A.nodes) == 87 and int(B.nodes) == 62 and close(float(B.useful_units), 644.9, 0.002)
          and close(float(A.useful_per_musd), 26.69, 0.003) and close(float(B.useful_per_musd), 31.49, 0.003)
          and close(float(B.useful_per_facility_mw), 645.0, 0.003))
    msg = (f"A {int(A.nodes)} nodes, {A.useful_per_musd}/$M, {A.useful_per_facility_mw}/MW; "
           f"B {int(B.nodes)} nodes, {B.useful_per_musd}/$M, {B.useful_per_facility_mw}/MW")
    hints = []
    if int(B.nodes) == 87:
        hints.append("B got 87 nodes (the cooling fit): B is power-bound, nodes = min(power fit 62, cooling fit 87)")
    if int(B.nodes) == 62 and close(float(B.useful_units), 644.9 / 0.93, 0.003):
        hints.append("B's useful units omit comm_efficiency (0.93 for the 2:1 spine)")
    return ok, hint(msg, hints)


def check_power_cap(c: Ctx) -> tuple[bool, str]:
    t = c.m.power_cap_tradeoff(c.b["curve"], c.b["cap_case"]).set_index("cap_w")
    best = c.m.best_cap(t.reset_index())
    ok = (int(t.loc[700, "nodes_per_rack"]) == 2 and int(t.loc[650, "nodes_per_rack"]) == 3
          and close(float(t.loc[650, "cluster_throughput"]), 47.52) and close(float(t.loc[700, "cluster_throughput"]), 32.0)
          and int(t.loc[700, "racks_needed_for_all"]) == 32 and close(float(t.loc[700, "unused_budget_kw"]), 9.1, 0.01)
          and best == 650)
    msg = (f"700 W: {t.loc[700, 'nodes_per_rack']}/rack, throughput {t.loc[700, 'cluster_throughput']}; "
           f"650 W: {t.loc[650, 'nodes_per_rack']}/rack, throughput {t.loc[650, 'cluster_throughput']}; best cap {best} W")
    hints = []
    if int(t.loc[700, "nodes_per_rack"]) == 3:
        hints.append("3 uncapped nodes per rack ignores the transient margin: budget = 32.78 kW x (1 - 0.10) = 29.5 kW")
    if best != 650 and best in (350, 400, 450, 500):
        hints.append(f"best cap {best} W maximises throughput per kW; rack slots bind, so pick the highest cluster throughput")
    return ok, hint(msg, hints)


def check_flags(c: Ctx) -> tuple[bool, str]:
    fc = c.m.forecast(c.b["plan"], c.a)
    f = c.m.misleading_nominal_flags(fc, c.m.compare_designs(c.b["designs"], c.a))
    exp = {"STRANDED_GPUS": ["2028Q2", "2028Q3", "2029Q2"], "RESERVE_SHORTFALL": ["2028Q3", "2029Q4"],
           "PER_GPU_COST_MISLEADS": ["B-liquid-nextgen"]}
    hints = [f"{k}: expected {v}, got {f.get(k)}" for k, v in exp.items() if f.get(k) != v]
    return f == exp, hint(f"{f}", hints if f != exp else [])


CHECKS: list[tuple[str, Callable[[Ctx], tuple[bool | None, str]]]] = [
    ("dataset reproducible", check_reproducible),
    ("T1 plan hygiene", check_clean),
    ("T2 usable fraction + kW per GPU", check_fractions),
    ("T2 quarterly forecast", check_forecast),
    ("T2 first shortfall + order deadlines", check_shortfall),
    ("T3 TCO and cost per GPU-hour", check_tco),
    ("T4 design comparison", check_designs),
    ("T5 power-capping trade-off", check_power_cap),
    ("T6 misleading-nominal flags", check_flags),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    try:
        ctx = Ctx(load_impl(args.impl))
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL import/load: {exc!r}")
        return 1
    passed = 0
    for name, fn in CHECKS:
        try:
            ok, msg = fn(ctx)
            if ok is None:
                print(f"SKIP {name}: {msg}")
                passed += 1
                continue
            print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}")
            passed += bool(ok)
        except NotImplementedError as exc:
            print(f"TODO {name}: implement {exc.args[0] if exc.args else 'function'}()")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            if args.verbose:
                print(traceback.format_exc())
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
