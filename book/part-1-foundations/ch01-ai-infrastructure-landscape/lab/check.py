#!/usr/bin/env python3
"""Checker for the Chapter 1 lab (workload-characterization model).

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
from typing import Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
PROFILES = DATA / "workload_profiles.csv"
PLATFORM = DATA / "platform_orion.yaml"

EXPECTED_ISSUES = {("W13", "MISSING"), ("W05", "DUPLICATE"), ("W15", "NEGATIVE"), ("W18", "BAD_UNIT")}
EXPECTED_CLASS = {
    "W01": "compute", "W02": "memory", "W03": "compute", "W04": "compute", "W05": "communication",
    "W06": "io", "W07": "io", "W08": "memory", "W09": "communication", "W10": "compute",
    "W11": "communication", "W12": "communication", "W16": "memory", "W17": "communication",
}
EXPECTED_FLAGS = {
    "IMPOSSIBLE": {"W12"},
    "LATENCY_OR_OVERHEAD": {"W16"},
    "MISLABELED": {"W05", "W09"},
}


def load_impl(impl: str) -> ModuleType:
    """Import workload_model.py from starter/ or ../solutions/lab/ by path."""
    path = HERE / "starter" / "workload_model.py" if impl == "starter" else \
        HERE.parent / "solutions" / "lab" / "workload_model.py"
    spec = importlib.util.spec_from_file_location(f"workload_model_{impl}", path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def close(a: float, b: float, rel: float = 0.005) -> bool:
    return math.isclose(a, b, rel_tol=rel, abs_tol=1e-12)


def _profile(**kw: float) -> dict:
    base = dict(workload_id="T", name="t", phase="other", declared_class="compute", gpus=8,
                tflop_per_gpu=0.0, hbm_gb_per_gpu=0.0, nvlink_gb_per_gpu=0.0, net_value_per_gpu=0.0,
                net_unit="GB", net_gb_per_gpu=0.0, io_read_gb_per_node=0.0, io_write_gb_per_node=0.0,
                observed_step_s=1.0)
    base.update(kw)
    return base


# ------------------------------------------------------------------ checks
class Skip(Exception):
    """Raised by a check that cannot run in this edition (e.g. generator stripped from student release)."""


def check_dataset_reproducible(m: ModuleType) -> tuple[bool, str]:
    gen = HERE / "tools" / "generate_profiles.py"
    if not gen.exists():
        raise Skip("generator not shipped in this edition (instructor material)")
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([sys.executable, str(gen), "--out", td],
                       check=True, capture_output=True)
        for name in ("workload_profiles.csv", "platform_orion.yaml"):
            a = hashlib.sha256((DATA / name).read_bytes()).hexdigest()
            b = hashlib.sha256((Path(td) / name).read_bytes()).hexdigest()
            if a != b:
                return False, f"{name} differs from regenerated copy (did you edit data/ by hand?)"
    return True, "generator reproduces committed data byte-for-byte"


def check_validation_issues(m: ModuleType) -> tuple[bool, str]:
    clean, issues = m.normalize_and_validate(m.load_csv(PROFILES))
    got = {(i["workload_id"], i["code"]) for i in issues}
    if got != EXPECTED_ISSUES:
        return False, f"issues {sorted(got)} != expected set of 4 (missing: {sorted(EXPECTED_ISSUES - got)})"
    if len(clean) != 14:
        return False, f"expected 14 clean rows, got {len(clean)}"
    names = {p["name"] for p in clean}
    if "moe-a2a-train-step" not in names or "moe-a2a-train-step-rerun" in names:
        return False, "duplicate handling must keep the FIRST occurrence of W05"
    return True, "4 bad rows rejected with correct codes, 14 clean rows"


def check_unit_normalization(m: ModuleType) -> tuple[bool, str]:
    clean, _ = m.normalize_and_validate(m.load_csv(PROFILES))
    by = {p["workload_id"]: p for p in clean}
    w11, w05 = by.get("W11"), by.get("W05")
    if w11 is None or not close(w11["net_gb_per_gpu"], 10.0):
        return False, f"W11 reports 80 Gb -> expected net_gb_per_gpu 10.0, got {w11 and w11.get('net_gb_per_gpu')}"
    if not close(w05["net_gb_per_gpu"], 60.0) or not isinstance(w05["gpus"], int):
        return False, "GB rows must pass through unchanged; gpus must be int"
    return True, "Gb -> GB conversion correct (80 Gb = 10 GB)"


def check_resource_times_core(m: ModuleType) -> tuple[bool, str]:
    plat = m.load_platform(PLATFORM)
    t = m.resource_times(_profile(tflop_per_gpu=989.0, hbm_gb_per_gpu=3350.0, nvlink_gb_per_gpu=900.0,
                                  net_gb_per_gpu=100.0), plat)
    want = {"compute": 1.0, "memory": 1.0, "scaleup": 2.0, "scaleout": 2.0, "io_read": 0.0, "io_write": 0.0}
    bad = [k for k, v in want.items() if k not in t or not close(t[k], v)]
    if bad:
        return False, f"wrong times for {bad}: got {{{', '.join(f'{k}: {t.get(k)}' for k in bad)}}}"
    return True, "compute/memory/NVLink/NIC ceilings applied correctly (NIC = 400/8 = 50 GB/s)"


def check_resource_times_io(m: ModuleType) -> tuple[bool, str]:
    plat = m.load_platform(PLATFORM)
    small = m.resource_times(_profile(gpus=8, io_read_gb_per_node=100.0, io_write_gb_per_node=100.0), plat)
    big = m.resource_times(_profile(gpus=256, io_read_gb_per_node=30.0, io_write_gb_per_node=30.6), plat)
    # 1 node: limited by frontend NICs (50 GB/s); 32 nodes: limited by PFS share (5 and 2.5 GB/s)
    ok = close(small["io_read"], 2.0) and close(small["io_write"], 2.0) and \
        close(big["io_read"], 6.0) and close(big["io_write"], 12.24)
    if not ok:
        return False, (f"1-node read/write {small['io_read']:.3g}/{small['io_write']:.3g} s (want 2/2); "
                       f"32-node read/write {big['io_read']:.3g}/{big['io_write']:.3g} s (want 6/12.24)")
    return True, "per-node I/O ceiling = min(frontend NICs, PFS aggregate / nodes in the job)"


def check_w01_worked_example(m: ModuleType) -> tuple[bool, str]:
    clean, _ = m.normalize_and_validate(m.load_csv(PROFILES))
    w01 = next(p for p in clean if p["workload_id"] == "W01")
    t = m.resource_times(w01, m.load_platform(PLATFORM))
    if not (close(t["compute"], 6875 / 989) and close(t["scaleup"], 1202.6 / 450) and close(t["scaleout"], 9.8 / 50)):
        return False, f"W01 compute {t['compute']:.3f} s (want 6.951), scaleup {t['scaleup']:.3f} s (want 2.672)"
    return True, "W01 (W-TRAIN) lower bounds match the Section 1.9 worked example"


def check_classification(m: ModuleType) -> tuple[bool, str]:
    out = m.analyze(PROFILES, PLATFORM)
    got = {r["workload_id"]: r["bound_class"] for r in out["results"]}
    wrong = {k: (got.get(k), v) for k, v in EXPECTED_CLASS.items() if got.get(k) != v}
    if wrong:
        return False, "misclassified (got, want): " + ", ".join(f"{k}={g}/{w}" for k, (g, w) in sorted(wrong.items()))
    return True, "all 14 clean workloads assigned the correct bound class"


def check_flags(m: ModuleType) -> tuple[bool, str]:
    out = m.analyze(PROFILES, PLATFORM)
    msgs = []
    for flag, want in EXPECTED_FLAGS.items():
        got = {r["workload_id"] for r in out["results"] if flag in r["flags"]}
        if got != want:
            msgs.append(f"{flag}: got {sorted(got)} want {sorted(want)}")
    if msgs:
        return False, "; ".join(msgs)
    w12 = next(r for r in out["results"] if r["workload_id"] == "W12")
    if not w12["ceiling_fraction"] > 1.0:
        return False, "W12 ceiling_fraction should exceed 1.0"
    return True, "IMPOSSIBLE=W12, LATENCY_OR_OVERHEAD=W16, MISLABELED=W05,W09"


def check_comparison(m: ModuleType) -> tuple[bool, str]:
    out = m.analyze(PROFILES, PLATFORM)
    by = {r["workload_id"]: r for r in out["results"]}
    md = m.comparison_markdown(by["W01"], by["W02"])
    need = ["W01", "W02", "compute", "memory", "scaleup", "scaleout", "io_read", "io_write",
            "Evidence to confirm", "|---"]
    missing = [n for n in need if n not in md]
    if missing:
        return False, f"comparison missing: {missing}"
    if sum(1 for line in md.splitlines() if line.startswith("|")) < 10:
        return False, "comparison table should have >= 10 table lines (header, rule, 6 resources, summary rows)"
    if len(md.split()) > 600:
        return False, "comparison should fit on one page (<= 600 words)"
    return True, "one-page W01 vs W02 comparison has all resources, bounds and evidence"


CHECKS: list[tuple[str, Callable[[ModuleType], tuple[bool, str]]]] = [
    ("dataset_reproducible", check_dataset_reproducible),
    ("validation_issues", check_validation_issues),
    ("unit_normalization", check_unit_normalization),
    ("resource_times_core", check_resource_times_core),
    ("resource_times_io", check_resource_times_io),
    ("w01_worked_example", check_w01_worked_example),
    ("classification", check_classification),
    ("flags", check_flags),
    ("comparison_markdown", check_comparison),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    ap.add_argument("-v", "--verbose", action="store_true", help="show tracebacks for failing checks")
    args = ap.parse_args()
    try:
        mod = load_impl(args.impl)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL import {args.impl}: {type(exc).__name__}: {exc}")
        return 2
    passed = skipped = 0
    for name, fn in CHECKS:
        try:
            ok, msg = fn(mod)
            status = "PASS" if ok else "FAIL"
        except Skip as exc:
            ok, status, msg = True, "SKIP", str(exc)
            skipped += 1
        except NotImplementedError as exc:
            ok, status, msg = False, "TODO", str(exc) or "not implemented"
        except Exception as exc:  # noqa: BLE001
            ok, status, msg = False, "FAIL", f"{type(exc).__name__}: {exc}"
            if args.verbose:
                traceback.print_exc(file=sys.stdout)
        passed += ok
        print(f"{status:4} {name:22} {msg}")
    print(f"\n{passed - skipped}/{len(CHECKS)} checks passed, {skipped} skipped ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
