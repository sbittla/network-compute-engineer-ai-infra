#!/usr/bin/env python3
"""Capstone C starter-kit checker — benchmark harness and scaling analysis.

Usage:
    python check.py                    # check your starter/harness.py and starter/analysis.py (default)
    python check.py --impl solution    # check the instructor reference (instructor edition only)

Prints one line per check (PASS / FAIL / TODO). Exits 0 only when every check passes.
Harness checks never test timing values (your laptop is not a GPU); they test discipline and numerics.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MODULES = ("harness", "analysis")


def load(impl: str, module: str) -> ModuleType | None:
    if impl == "solution":
        path = HERE.parent / "instructor" / "reference" / f"{module}.py"
    else:
        path = HERE / "starter" / f"{module}.py"
    if not path.exists():
        print(f"Implementation not found: {path}")
        if impl == "solution":
            print("The instructor reference is not shipped in the student edition.")
        return None
    spec = importlib.util.spec_from_file_location(f"{module}_{impl}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CHECKS: list[tuple[str, Callable[[], str]]] = []
_C: dict[str, object] = {}
M: dict[str, ModuleType] = {}


def check(name: str):
    def deco(fn: Callable[[], str]):
        CHECKS.append((name, fn))
        return fn
    return deco


def close(a: float, b: float, rel: float = 1e-6) -> bool:
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)


def an() -> ModuleType:
    return M["analysis"]


def data():
    if "data" not in _C:
        m = an()
        runs, man = m.load_runs(DATA)
        st = m.steady_state(runs)
        s = m.run_summary(st)
        _C["data"] = (runs, man, st, s)
    return _C["data"]


def valid():
    if "valid" not in _C:
        runs, man, _, s = data()
        _C["valid"] = an().validate_runs(runs, man, s)
    return _C["valid"]


# ---- harness checks ------------------------------------------------------------------------------

@check("H1 ring_allreduce correctness + bytes")
def _h1():
    h = M["harness"]
    rng = np.random.default_rng(3)
    for n in (1, 2, 3, 4, 5):
        for length in (10001, 7, 3):
            bufs = [rng.standard_normal(length) for _ in range(n)]
            res, sent = h.ring_allreduce(bufs)
            ref = np.sum(bufs, axis=0)
            assert len(res) == n and all(np.allclose(r, ref, rtol=1e-12, atol=1e-12) for r in res), \
                f"n={n} L={length}: results differ from the elementwise sum on some rank"
            assert sum(sent) == 2 * (n - 1) * length * 8, \
                f"n={n} L={length}: total bytes {sum(sent)} != 2(n-1) x L x 8"
    return "sums correct for n=1..5 incl. lengths not divisible by n; bytes = 2(n-1)L x 8"


@check("H2 summarize statistics")
def _h2():
    t = [0.9, 1.0, 1.1, 1.05, 3.0, 0.95, 1.02]
    s = M["harness"].summarize(t)
    a = np.asarray(t)
    p25, p50, p75, p95 = np.percentile(a, [25, 50, 75, 95])
    for k, v in {"median": p50, "p95": p95, "iqr": p75 - p25, "min": 0.9, "max": 3.0,
                 "cv": a.std(ddof=1) / a.mean()}.items():
        assert close(s[k], v), f"{k}: {s[k]} != {v}"
    return "median/p95/IQR/CV match numpy (linear interpolation, ddof=1)"


@check("H3 run_benchmark discipline")
def _h3():
    h = M["harness"]
    r1 = h.run_benchmark(n_ranks=4, dim=48, grad_elems=10001, warmup=2, reps=5, seed=11)
    r2 = h.run_benchmark(n_ranks=4, dim=48, grad_elems=10001, warmup=2, reps=5, seed=11)
    assert len(r1["times_s"]) == 5 and len(r1["compute_s"]) == 5 and len(r1["comm_s"]) == 5, \
        "record only the measured repetitions, not warm-up"
    assert all(abs(c + m - t) < 1e-3 for c, m, t in zip(r1["compute_s"], r1["comm_s"], r1["times_s"])), \
        "times_s should equal compute_s + comm_s per iteration"
    rng = np.random.default_rng(11)
    for _ in range(8):
        rng.standard_normal((48, 48))
    last = None
    for _ in range(7):
        last = [rng.standard_normal(10001) for _ in range(4)]
    exp = float(np.sum(last, axis=0).sum())
    assert close(r1["checksum"], exp, 1e-9) and r1["checksum"] == r2["checksum"], \
        f"checksum {r1['checksum']} != {exp}: draw all A, all B, then per-iteration grads from default_rng(seed)"
    assert r1["summary"]["n"] == 5, "summary must cover measured reps only"
    return "warm-up excluded, compute + comm = total, numerics deterministic"


@check("H4 manifest and evidence label")
def _h4():
    h = M["harness"]
    man = h.capture_manifest(7)
    need = ["python", "numpy", "platform", "machine", "processor", "cpu_count", "blas", "seed",
            "timestamp_utc", "evidence_class"]
    miss = [k for k in need if k not in man]
    assert not miss, f"manifest missing {miss}"
    lab = h.run_benchmark(n_ranks=2, dim=16, grad_elems=100, warmup=1, reps=2, seed=1)["evidence_label"]
    assert "MEASURED" in lab and "CPU proxy" in lab and "not GPU" in lab, f"evidence label too weak: {lab!r}"
    return "manifest complete; label says CPU proxy, not GPU evidence"


# ---- analysis checks -----------------------------------------------------------------------------

@check("A1 steady_state (warm-up and restart)")
def _a1():
    _, _, st, _ = data()
    n19 = int((st["run_id"] == "r0419").sum())
    assert n19 == 56, f"r0419 keeps {n19} steps; expected (42 - 5) + (24 - 5) = 56 (second warm-up after restart)"
    assert len(st) == 95 * 55 + 56, f"{len(st)} steady-state rows, expected {95 * 55 + 56}"
    return "first 5 steps of each run and of each restart removed"


@check("A2 run_summary")
def _a2():
    _, _, st, s = data()
    g = st[st["run_id"] == "r0401"]["step_time_s"].to_numpy()
    row = s.set_index("run_id").loc["r0401"]
    assert close(row["median_s"], float(np.median(g))), f"median {row['median_s']}"
    assert close(row["p95_s"], float(np.percentile(g, 95))), f"p95 {row['p95_s']}"
    assert len(s) == 96, f"{len(s)} runs summarized, expected 96"
    return "per-run median / p95 / IQR / CV"


@check("A3 validate_runs (admissibility)")
def _a3():
    v = valid().set_index("run_id")
    bad = sorted(v.index[~v["valid"].astype(bool)])
    assert bad == ["r0419", "r0421", "r0444", "r0458"], f"invalid runs {bad}; four runs fail the admissibility rules"
    assert "restarted" in v.at["r0419", "reasons"], "r0419 reason"
    assert "nccl_version" in v.at["r0444", "reasons"], "r0444 reason should name the NCCL version"
    assert "outlier" in v.at["r0458", "reasons"] and "outlier" in v.at["r0421", "reasons"], "outlier reasons"
    return "restart, environment drift and two statistical outliers (one with a documented cause) caught"


@check("A4 weak-scaling table")
def _a4():
    _, _, _, s = data()
    t = an().scaling_table(s, valid()).set_index(["variant", "n_gpus"])
    assert int(t.at[("baseline", 128), "n_runs"]) == 6 and int(t.at[("ib_gdr", 256), "n_runs"]) == 7, \
        "invalid runs must be excluded"
    eb = t.at[("baseline", 256), "weak_scaling_eff"]
    eo = t.at[("ib_gdr", 256), "weak_scaling_eff"]
    assert abs(eb - 0.842) < 0.005, f"baseline efficiency at 256 GPUs {eb:.3f}, expected ~0.842"
    assert abs(eo - 0.979) < 0.005, f"ib_gdr efficiency at 256 GPUs {eo:.3f}, expected ~0.979"
    return f"weak-scaling efficiency at 256 GPUs: baseline {eb:.3f}, ib_gdr {eo:.3f}"


@check("A5 permutation test")
def _a5():
    m = an()
    assert close(m.permutation_pvalue([1, 2, 3], [4, 5, 6]), 0.1), "exact p for [1,2,3] vs [4,5,6] is 2/20 = 0.1"
    assert close(m.permutation_pvalue([1, 1], [1, 1]), 1.0), "identical samples -> p = 1"
    adj = m.holm([0.01, 0.04, 0.03, 0.5])
    assert all(close(x, y) for x, y in zip(adj, [0.04, 0.09, 0.09, 0.5])), f"Holm-adjusted {adj}, expected [0.04, 0.09, 0.09, 0.5]"
    return "exact two-sided permutation p-values; Holm step-down adjustment"


@check("A6 variant comparisons + significance")
def _a6():
    m = an()
    _, _, _, s = data()
    fam = m.compare_family(s, valid(), [("baseline", "ib_gdr"), ("ib_gdr", "ib_gdr_bucket")])
    assert len(fam) == 8 and "p_holm" in fam.columns, "8 tests in the family, Holm-adjusted"
    c1 = fam[fam["comparison"] == "baseline->ib_gdr"].set_index("n_gpus")
    c2 = fam[fam["comparison"] == "ib_gdr->ib_gdr_bucket"].set_index("n_gpus")
    sig1 = sorted(int(n) for n in c1.index[c1["significant"].astype(bool)])
    assert sig1 == [32, 64, 128, 256], f"baseline -> ib_gdr significant (Holm) at {sig1}"
    assert abs(c1.at[256, "speedup"] - 1.176) < 0.005, f"speedup at 256 GPUs {c1.at[256, 'speedup']:.3f}"
    assert not c2["significant"].astype(bool).any(), "the bucket change should not be significant at any scale"
    return "transport fix significant at every scale after Holm (8 tests); bucket tweak nowhere"


@check("A7 exposed communication (profile)")
def _a7():
    e = an().exposed_comm(pd.read_csv(DATA / "profile_summary.csv")).set_index(["variant", "n_gpus"])
    fb, fo = e.at[("baseline", 256), "exposed_comm_fraction"], e.at[("ib_gdr", 256), "exposed_comm_fraction"]
    assert abs(fb - 0.153) < 0.003 and abs(fo - 0.0075) < 0.002, f"exposed fractions baseline {fb:.3f}, ib_gdr {fo:.4f}"
    assert e.at[("baseline", 256), "memcpy_busy_ms"] > 1000, "host bounce-buffer copies are the GDR-off signature"
    return f"exposed comm {fb:.1%} -> {fo:.1%} of step at 256 GPUs"


@check("A8 NCCL transport from debug log")
def _a8():
    m = an()
    b = m.nccl_transport((DATA / "nccl_debug_baseline.log").read_text(encoding="utf-8"))
    o = m.nccl_transport((DATA / "nccl_debug_ib_gdr.log").read_text(encoding="utf-8"))
    assert b["network"] == "Socket" and b["no_ib_device"] and not b["gdr"], f"baseline {b}"
    assert o["network"] == "IB" and o["gdr"] and len(o["ib_devices"]) == 8, f"ib_gdr {o}"
    return "baseline fell back to NET/Socket; fix uses NET/IB with GDRDMA on 8 HCAs"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    for name in MODULES:
        try:
            mod = load(args.impl, name)
        except Exception as e:  # syntax error etc. in learner code
            print(f"FAIL import {name}  {type(e).__name__}: {e}")
            return 1
        if mod is None:
            return 2
        M[name] = mod
    counts = {"PASS": 0, "FAIL": 0, "TODO": 0}
    for name, fn in CHECKS:
        try:
            msg = fn()
            status = "PASS"
        except NotImplementedError as e:
            status, msg = "TODO", str(e) or "not implemented yet"
        except AssertionError as e:
            status, msg = "FAIL", str(e) or "assertion failed"
        except Exception as e:  # noqa: BLE001 - report, never crash
            status, msg = "FAIL", f"{type(e).__name__}: {e}"
        counts[status] += 1
        print(f"{status:4} {name:<40} {msg}")
    total = len(CHECKS)
    print(f"\n{counts['PASS']}/{total} checks pass ({counts['TODO']} TODO, {counts['FAIL']} FAIL) [impl={args.impl}]")
    return 0 if counts["PASS"] == total else 1


if __name__ == "__main__":
    sys.exit(main())
