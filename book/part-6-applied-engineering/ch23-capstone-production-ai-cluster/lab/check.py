#!/usr/bin/env python3
"""Checker for the Chapter 23 lab: capstone design-review linter.

Usage:
    python check.py                    # checks starter/design_lint.py (your work)
    python check.py --impl solution    # checks the reference implementation (instructors)

Prints one PASS / FAIL / TODO line per check. Exit code 0 only if every check passes.
No hardware, no network, no root; runs in well under 60 s.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FLAWED = DATA / "bundle_kestrel_capA"
CLEAN = DATA / "bundle_orion_reference"

# The planted findings in the flawed bundle, as (rule, location) pairs. A correct linter reports
# exactly this set -- no more (false positives) and no fewer (misses).
EXPECTED_FLAWED: dict[str, set[tuple[str, str]]] = {
    "check_completeness": {("COMP-001", "design.md:Failure exercise"),
                           ("COMP-002", "assumptions.yaml:A-07.validation"),
                           ("COMP-002", "slos.yaml:SLO-03.window")},
    "check_capacity": {("GPU-001", "bom.yaml:gpu_nodes"),
                       ("GPU-002", "assumptions.yaml:workload.parallelism")},
    "check_fabric": {("PORT-001", "topology.yaml:rail_leaf"),
                     ("PORT-002", "topology.yaml:claimed_oversubscription"),
                     ("CABLE-001", "bom.yaml:cables.backend_400g")},
    "check_power": {("POWER-001", "bom.yaml:racks.rack-07"), ("POWER-001", "bom.yaml:racks.rack-08")},
    "check_evidence": {("EVID-001", "benchmarks.md:B-03"), ("EVID-002", "benchmarks.md:B-05"),
                       ("EVID-003", "benchmarks.md:B-02"), ("EVID-004", "benchmarks.md:B-04")},
    "check_unlabeled_numbers": {("NUM-001", "design.md:L18"), ("NUM-001", "design.md:L29")},
    "check_cross_refs": {("XREF-001", "design.md:A-12")},
    "check_failure_domains": {("FD-001", "failure_domains.yaml:FD-06"),
                              ("FD-002", "failure_domains.yaml:scheduler")},
    "check_slos": {("SLO-001", "slos.yaml:SLO-04.target")},
}


def load_impl(impl: str) -> ModuleType:
    path = (HERE / "starter" / "design_lint.py") if impl == "starter" else (
        HERE.parent / "solutions" / "lab" / "design_lint.py")
    spec = importlib.util.spec_from_file_location(f"design_lint_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def keys(findings: list[dict]) -> set[tuple[str, str]]:
    return {(f["rule"], f["location"]) for f in findings}


def diff_msg(got: set, want: set) -> str:
    missing, extra = sorted(want - got), sorted(got - want)
    parts = []
    if missing:
        parts.append(f"missing {missing}")
    if extra:
        parts.append(f"unexpected {extra}")
    return "; ".join(parts) or "ok"


def make_rule_check(name: str) -> Callable[[ModuleType], str]:
    def _check(m: ModuleType) -> str:
        fn = getattr(m, name)
        flawed, clean = m.load_bundle(FLAWED), m.load_bundle(CLEAN)
        got = keys(fn(flawed))
        want = EXPECTED_FLAWED[name]
        assert got == want, f"flawed bundle: {diff_msg(got, want)}"
        fp = keys(fn(clean))
        assert not fp, f"false positives on the clean reference bundle: {sorted(fp)}"
        for f in fn(flawed):
            assert f["severity"] == m.RULES[f["rule"]][0], f"wrong severity on {f}"
            assert f.get("message"), f"empty message on {f}"
        return f"{len(want)} planted finding(s) found, 0 false positives"
    _check.__name__ = name
    return _check


def check_edge_cases(m: ModuleType) -> str:
    """Rules with no planted instance still have to work: mutate the clean bundle in memory."""
    base = m.load_bundle(CLEAN)

    b = copy.deepcopy(base)                       # 2 declared spares: 34 nodes, 256 GPUs is fine
    b["bom.yaml"]["gpu_nodes"].update({"count": 34, "spares": 2})
    b["bom.yaml"]["racks"]["gpu_racks"]["R9"] = 2
    got = keys(m.check_capacity(b))
    assert got == set(), f"declared spares should satisfy GPU-001/GPU-003, got {sorted(got)}"

    b["bom.yaml"]["racks"]["gpu_racks"]["R9"] = 1  # racks now hold 33 of 34 nodes
    got = keys(m.check_capacity(b))
    assert got == {("GPU-003", "bom.yaml:racks.gpu_racks")}, f"GPU-003 not raised: {sorted(got)}"

    b = copy.deepcopy(base)                       # 3:1 leaf: 48 down, 16 up, claim "3:1"
    b["topology.yaml"]["backend"]["rail_leaf"].update(
        {"downlinks": 48, "uplinks": 16, "uplinks_per_spine": 4})
    b["topology.yaml"]["backend"]["claimed_oversubscription"] = "3:1"
    b["bom.yaml"]["gpu_nodes"]["count"] = 48
    b["bom.yaml"]["cables"]["backend_400g"] = 8 * 64
    got = keys(m.check_fabric(b))
    assert got == set(), f"a correct 3:1 design must be clean, got {sorted(got)}"

    b["topology.yaml"]["backend"]["rail_leaf"]["uplinks_per_spine"] = 9   # 8 x 9 = 72 > 64
    b["bom.yaml"]["gpu_nodes"]["count"] = 47
    got = keys(m.check_fabric(b))
    assert ("PORT-003", "topology.yaml:spine") in got, f"PORT-003 not raised: {sorted(got)}"
    assert ("PORT-004", "topology.yaml:rail_leaf") in got, f"PORT-004 not raised: {sorted(got)}"

    b = copy.deepcopy(base)                       # exactly at budget is allowed
    b["bom.yaml"]["racks"]["budget_kw"] = 40.8
    got = keys(m.check_power(b))
    assert got == set(), f"4 x 10.2 = 40.8 kW at a 40.8 kW budget must pass, got {sorted(got)}"

    b = copy.deepcopy(base)                       # missing file is a COMP-001 blocker
    b["slos.yaml"] = None
    got = keys(m.check_completeness(b))
    assert ("COMP-001", "slos.yaml") in got, f"missing file not reported: {sorted(got)}"
    return "spares, GPU-003, 3:1 fabric, PORT-003/004, power boundary, missing file"


def check_run_lint_flawed(m: ModuleType) -> str:
    res = m.run_lint(m.load_bundle(FLAWED))
    want = set().union(*EXPECTED_FLAWED.values())
    got = keys(res["findings"])
    assert got == want, diff_msg(got, want)
    assert res["counts"] == {"blocker": 6, "major": 14, "minor": 0}, f"counts {res['counts']}"
    assert res["gate"] == "FAIL", f"gate should be FAIL, got {res['gate']}"
    order = [m.SEVERITY_ORDER[f["severity"]] for f in res["findings"]]
    assert order == sorted(order), "findings not sorted blockers-first"
    return "20 findings (6 blocker, 14 major), gate FAIL"


def check_run_lint_clean(m: ModuleType) -> str:
    res = m.run_lint(m.load_bundle(CLEAN))
    assert res["findings"] == [], f"clean bundle produced {keys(res['findings'])}"
    assert res["gate"] == "PASS", f"gate should be PASS, got {res['gate']}"
    return "0 findings, gate PASS"


def check_report(m: ModuleType) -> str:
    res = m.run_lint(m.load_bundle(FLAWED))
    rep = m.render_report(res, "bundle_kestrel_capA")
    assert "Gate: FAIL" in rep, "report lacks 'Gate: FAIL'"
    for rule, loc in keys(res["findings"]):
        assert rule in rep and loc in rep, f"report lacks {rule} at {loc}"
    rep2 = m.render_report(m.run_lint(m.load_bundle(CLEAN)), "bundle_orion_reference")
    assert "Gate: PASS" in rep2, "clean report lacks 'Gate: PASS'"
    return "report lists every finding and the gate verdict"


CHECKS: list[Callable[[ModuleType], str]] = [make_rule_check(n) for n in EXPECTED_FLAWED] + [
    check_edge_cases, check_run_lint_flawed, check_run_lint_clean, check_report]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    t0 = time.perf_counter()
    try:
        mod = load_impl(args.impl)
    except Exception as exc:  # noqa: BLE001 -- report, never traceback
        print(f"FAIL import  could not import {args.impl} implementation: {exc!r}")
        return 1
    passed = todo = failed = 0
    for chk in CHECKS:
        try:
            msg = chk(mod)
            print(f"PASS {chk.__name__:26s} {msg}")
            passed += 1
        except NotImplementedError as exc:
            print(f"TODO {chk.__name__:26s} {exc}")
            todo += 1
        except AssertionError as exc:
            print(f"FAIL {chk.__name__:26s} {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {chk.__name__:26s} {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed}/{len(CHECKS)} passed, {todo} TODO, {failed} failed "
          f"({time.perf_counter() - t0:.2f}s, impl={args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
