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
    return ok, (f"2028Q2 energized/stranded={r.loc['2028Q2', 'energized']}/{r.loc['2028Q2', 'stranded']}; "
                f"2028Q3 usable {r.loc['2028Q3', 'usable']} vs required {r.loc['2028Q3', 'required']} -> {r.loc['2028Q3', 'status']}")


def check_shortfall(c: Ctx) -> tuple[bool, str]:
    fc = c.m.forecast(c.b["plan"], c.a)
    q = c.m.first_shortfall(fc)
    d = c.m.order_deadlines(q, c.a)
    ok = q == "2028Q3" and d == {"gpus": "2028Q1", "network": "2028Q2", "facility_power": "2027Q3"}
    return ok, f"first shortfall={q}; order-by={d}"


def check_tco(c: Ctx) -> tuple[bool, str]:
    t = c.m.tco(32, ORION, c.a, fixed_capex_usd=2_000_000)
    ok = (close(t["total"], 6_767_309, 0.001) and close(t["usd_per_nominal_gpu_h"], 3.018, 0.002)
          and close(t["usd_per_allocated_gpu_h"], 4.179, 0.002) and close(t["usd_per_useful_gpu_h"], 4.748, 0.002))
    return ok, (f"ORION-256 TCO ${t['total']/1e6:.2f}M/yr; $/GPU-h nominal {t['usd_per_nominal_gpu_h']:.2f}, "
                f"allocated {t['usd_per_allocated_gpu_h']:.2f}, useful {t['usd_per_useful_gpu_h']:.2f} (expect 3.02/4.18/4.75)")


def check_designs(c: Ctx) -> tuple[bool, str]:
    d = c.m.compare_designs(c.b["designs"], c.a).set_index("design")
    A, B = d.loc["A-air-H100class"], d.loc["B-liquid-nextgen"]
    ok = (int(A.nodes) == 87 and int(B.nodes) == 62 and close(float(B.useful_units), 644.9, 0.002)
          and close(float(A.useful_per_musd), 26.53, 0.003) and close(float(B.useful_per_musd), 31.36, 0.003)
          and close(float(B.useful_per_facility_mw), 645.0, 0.003))
    return ok, (f"A {int(A.nodes)} nodes, {A.useful_per_musd}/$M, {A.useful_per_facility_mw}/MW; "
                f"B {int(B.nodes)} nodes, {B.useful_per_musd}/$M, {B.useful_per_facility_mw}/MW")


def check_power_cap(c: Ctx) -> tuple[bool, str]:
    t = c.m.power_cap_tradeoff(c.b["curve"], c.b["cap_case"]).set_index("cap_w")
    best = c.m.best_cap(t.reset_index())
    ok = (int(t.loc[700, "nodes_per_rack"]) == 2 and int(t.loc[650, "nodes_per_rack"]) == 3
          and close(float(t.loc[650, "cluster_throughput"]), 47.52) and close(float(t.loc[700, "cluster_throughput"]), 32.0)
          and int(t.loc[700, "racks_needed_for_all"]) == 32 and close(float(t.loc[700, "unused_budget_kw"]), 9.1, 0.01)
          and best == 650)
    return ok, (f"700 W: {t.loc[700, 'nodes_per_rack']}/rack, throughput {t.loc[700, 'cluster_throughput']}; "
                f"650 W: {t.loc[650, 'nodes_per_rack']}/rack, throughput {t.loc[650, 'cluster_throughput']}; best cap {best} W")


def check_flags(c: Ctx) -> tuple[bool, str]:
    fc = c.m.forecast(c.b["plan"], c.a)
    f = c.m.misleading_nominal_flags(fc, c.m.compare_designs(c.b["designs"], c.a))
    exp = {"STRANDED_GPUS": ["2028Q2", "2028Q3", "2029Q2"], "RESERVE_SHORTFALL": ["2028Q3", "2029Q4"],
           "PER_GPU_COST_MISLEADS": ["B-liquid-nextgen"]}
    return f == exp, f"{f}"


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
