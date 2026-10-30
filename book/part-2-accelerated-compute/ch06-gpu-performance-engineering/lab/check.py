#!/usr/bin/env python3
"""Checker for the Chapter 6 lab (benchmark harness, statistics, decisions, roofline).

Usage:
    python check.py                    # check starter/harness.py and starter/analysis.py
    python check.py --impl solution    # instructor reference (not in the student release)

Prints one PASS / FAIL / TODO line per check; exit 0 only if every check passes. The harness check runs
a tiny live microbenchmark but asserts only structure (sample counts, manifest keys, arithmetic), never
timing values. Expected statistics are computed here independently with numpy.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import os
import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
REF = {"driver": "570.124.06", "cuda": "12.8", "torch": "2.4.0"}


def load(impl: str, name: str):
    path = (HERE / "starter" / name) if impl == "starter" else (HERE.parent / "solutions" / "lab" / name)
    if not path.exists():
        print(f"Implementation not found: {path}\n(The solutions folder is removed from the student release.)")
        sys.exit(2)
    spec = importlib.util.spec_from_file_location(f"ch06_{impl}_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        assert spec.loader is not None
        spec.loader.exec_module(mod)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL import — could not import {path.name}: {type(exc).__name__}: {exc}")
        sys.exit(1)
    return mod


def csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name, dtype={"cuda": str})


# ---- harness checks -----------------------------------------------------------------------
def c_time_samples(h, a):
    ticks = iter(range(0, 10_000, 7))  # fake timer: every call advances 7 ns, deterministic
    s = h.time_samples(lambda: None, warmup=2, reps=5, timer=lambda: next(ticks))
    assert len(s["warmup_ns"]) == 2 and len(s["samples_ns"]) == 5, "warm-up must be separated from samples"
    assert all(x == 7 for x in s["samples_ns"]), "each call must be timed individually"
    try:
        h.time_samples(lambda: None, warmup=0, reps=0)
        raise AssertionError("reps=0 must raise ValueError")
    except ValueError:
        pass
    return "warm-up separated, per-call timing, argument validation"


def c_summarize_ns(h, a):
    s = h.summarize_ns([1_000_000, 2_000_000, 3_000_000, 4_000_000], work=2e9, unit="GFLOP/s")
    assert abs(s["median_ms"] - 2.5) < 1e-12 and abs(s["iqr_ms"] - 1.5) < 1e-12, f"median/IQR wrong: {s}"
    assert abs(s["rate_median"] - 2e9 / 2.5e-3 / 1e9) < 1e-9 and s["unit"] == "GFLOP/s", "rate must use the median time"
    assert s["n"] == 4 and s["min_ms"] == 1.0 and s["max_ms"] == 4.0
    return "median 2.5 ms, IQR 1.5 ms, 800 GFLOP/s on synthetic samples"


def c_benches(h, a):
    fn, flop = h.matmul_bench(64, seed=3)
    assert flop == 2 * 64 ** 3, "matmul FLOP must be 2n^3"
    r1, r2 = fn(), fn()
    assert r1.shape == (64, 64) and np.array_equal(r1, r2), "inputs must be created once (deterministic)"
    fn2, moved = h.copy_bench(1 << 20)
    fn2()
    assert moved == 2 * (1 << 20), "copy moves each byte twice (read + write)"
    return "matmul 2n^3 FLOP, copy 2x bytes, deterministic inputs"


def c_manifest(h, a):
    m = h.environment_manifest(seed=9)
    missing = [k for k in h.MANIFEST_KEYS if k not in m]
    assert not missing, f"manifest missing {missing}"
    assert m["seed"] == 9 and m["numpy"] == np.__version__ and m["python"] == sys.version.split()[0]
    assert m["pid"] == os.getpid(), "manifest must record the process id"
    s = h.run_suite(quick=True, warmup=1, reps=3)
    assert len(s["results"]) == 4 and all(len(r["samples_ns"]) == 3 for r in s["results"])
    assert s["config"]["warmup"] == 1 and "manifest" in s
    return "manifest complete (incl. pid); suite records raw samples and config"


def c_independent(h, a):
    runs = h.run_independent(2, quick=True, warmup=1, reps=2)
    pids = [r["manifest"]["pid"] for r in runs]
    assert len(runs) == 2 and len(set(pids)) == 2, f"runs must be separate processes, got pids {pids}"
    assert os.getpid() not in pids, "runs must not execute in the checker's own process"
    return f"2 runs in fresh processes (pids {pids[0]}, {pids[1]})"


# ---- statistics checks ----------------------------------------------------------------------
def c_quantile(h, a):
    rng = np.random.default_rng(0)
    for n in (1, 2, 7, 50):
        x = rng.normal(size=n)
        for q in (0.0, 0.05, 0.25, 0.5, 0.75, 0.99, 1.0):
            assert abs(a.quantile(x, q) - float(np.quantile(x, q))) < 1e-12, f"quantile n={n} q={q}"
    s = a.summarize([1, 2, 3, 4, 100])
    assert s["median"] == 3 and abs(s["iqr"] - 2.0) < 1e-12 and abs(s["p95"] - float(np.quantile([1, 2, 3, 4, 100], .95))) < 1e-12
    assert abs(s["cv"] - float(np.std([1, 2, 3, 4, 100], ddof=1) / 22.0)) < 1e-12
    return "matches numpy linear quantiles; summary fields correct"


def c_cliff(h, a):
    assert a.cliffs_delta([1, 2], [3, 4]) == -1.0 and a.cliffs_delta([3, 4], [1, 2]) == 1.0
    assert a.cliffs_delta([1, 2, 3], [1, 2, 3]) == 0.0
    assert abs(a.cliffs_delta([1, 5], [2, 3, 4]) - 0.0) < 1e-12
    return "sign and tie handling correct"


def c_clean(h, a):
    cb, eb = a.clean_runs(csv("bench_baseline.csv"), REF)
    cc, ec = a.clean_runs(csv("bench_candidate_b.csv"), REF)
    assert [(e["run_id"], e["reason"]) for e in eb] == [("A3", "version")], f"baseline exclusions {eb}"
    assert [(e["run_id"], e["reason"]) for e in ec] == [("B4", "clocks")], f"candidate B exclusions {ec}"
    assert cb["iter"].min() == 5 and len(cb) == 5 * 55 and len(cc) == 5 * 55, "warm-up iterations must be dropped"
    c2, e2 = a.clean_runs(csv("bench_candidate_c.csv"), REF)
    assert not e2 and len(c2) == 6 * 55, "candidate C has no bad runs (sw_power_cap is routine) and no warm-up rows"
    return "A3 (torch 2.3.1) and B4 (thermal, clock 21 % below peers) excluded; routine power-cap events kept"


def _boot(b, c, n_boot, seed):
    rng = np.random.default_rng(seed)
    reps = []
    for _ in range(n_boot):
        bi = rng.integers(0, len(b), len(b))
        ci = rng.integers(0, len(c), len(c))
        reps.append(np.median(c[ci]) / np.median(b[bi]) - 1)
    return float(np.quantile(reps, 0.025)), float(np.quantile(reps, 0.975))


def c_bootstrap(h, a):
    b = np.array([4.02, 4.006, 3.99, 4.0, 4.005])
    c = np.array([3.89, 3.87, 3.88, 3.879, 3.878])
    p, lo, hi = a.bootstrap_ratio_ci(b, c, n_boot=500, seed=3)
    elo, ehi = _boot(b, c, 500, 3)
    assert abs(p - (np.median(c) / np.median(b) - 1)) < 1e-12, "point estimate = ratio of medians - 1"
    assert abs(lo - elo) < 1e-12 and abs(hi - ehi) < 1e-12, f"CI ({lo:.5f},{hi:.5f}) != expected ({elo:.5f},{ehi:.5f}); follow the RNG recipe"
    assert lo <= p <= hi
    return f"point {p:+.3%}, 95 % CI [{lo:+.3%}, {hi:+.3%}] reproduces the documented recipe"


def c_permutation(h, a):
    p = a.permutation_test(np.array([1.0, 2.0, 3.0]), np.array([4.0, 5.0, 6.0]))
    assert abs(p - 2 / 20) < 1e-12, f"fully separated 3 vs 3 must give p = 2/C(6,3) = 0.1, got {p}"
    p2 = a.permutation_test(np.array([1.0, 3.0, 5.0]), np.array([2.0, 4.0, 6.0]))
    assert 0.5 < p2 <= 1.0, "interleaved groups must not be significant"
    assert abs(a.mde(0.01, 8) - 2.8 * 0.01 * 0.5) < 1e-12, "MDE = 2.8 * sigma * sqrt(2/n)"
    return "exact enumeration correct; MDE formula correct"


def c_decisions(h, a):
    floor = a.noise_floor(csv("bench_aa.csv"), REF)
    assert 0.002 < floor < 0.02, f"A/A noise floor {floor:.3%} implausible"
    base = csv("bench_baseline.csv")
    rb = a.compare(base, csv("bench_candidate_b.csv"), REF, floor)
    rc = a.compare(base, csv("bench_candidate_c.csv"), REF, floor)
    assert rb["naive"] > 0, "naive mean comparison of B should (wrongly) show a regression"
    assert rb["decision"] == "improvement" and -0.04 < rb["point"] < -0.025, f"B: {rb['decision']} {rb['point']:+.3%}"
    assert abs(rb["p_perm"] - 2 / 252) < 1e-12, f"B is fully separated: exact p = 2/252, got {rb['p_perm']:.4f}"
    assert rc["naive"] < -0.01, "naive mean comparison of C should (wrongly) show >1 % improvement"
    assert rc["decision"] == "below_threshold" and abs(rc["point"]) < 0.01, f"C: {rc['decision']} {rc['point']:+.3%}"
    assert rb["cliffs_delta_runs"] == -1.0 and rb["cliffs_delta_iter"] < -0.474, "B's effect size should be large at both levels"
    return (f"floor ±{floor:.2%}; B naive {rb['naive']:+.2%} -> {rb['point']:+.2%} p={rb['p_perm']:.3f} {rb['decision']}; "
            f"C naive {rc['naive']:+.2%} -> {rc['point']:+.2%} p={rc['p_perm']:.3f} {rc['decision']}")


# ---- roofline checks ------------------------------------------------------------------------
def c_roofline(h, a):
    dev = yaml.safe_load((DATA / "device.yaml").read_text(encoding="utf-8"))
    assert abs(a.ridge_point(989e12, 3.35e12) - 295.2238806) < 1e-6
    assert a.attainable(10, 989e12, 3.35e12) == 33.5e12 and a.attainable(1000, 989e12, 3.35e12) == 989e12
    k = a.classify_kernels(pd.read_csv(DATA / "kernels.csv"), dev).set_index("name")
    expect = {"gemm_bf16_8192x8192x8192": "compute", "gemm_bf16_decode_m16": "memory", "layernorm_fwd_bf16": "memory",
              "flash_attn_fwd_bf16": "compute", "fp32_simt_stencil": "compute", "bias_add_l2_resident": "anomaly",
              "gemm_fp8_8192x8192x8192": "compute", "embedding_gather_bf16": "memory", "gemm_bf16_4096x4096x512": "compute"}
    got = k["bound"].to_dict()
    bad = {n: (got.get(n), v) for n, v in expect.items() if got.get(n) != v}
    assert not bad, f"misclassified (got, expected): {bad}"
    f32 = k.loc["fp32_simt_stencil"]
    assert abs(f32["ridge"] - 67e12 / 3.35e12) < 1e-9 and abs(f32["pct_of_roof"] - 5e11 / 8780e-6 / 67e12) < 1e-9, \
        "the FP32 SIMT kernel must be judged against the FP32 ceiling"
    assert abs(k.loc["gemm_fp8_8192x8192x8192", "ridge"] - 1979e12 / 3.35e12) < 1e-6
    dec = k.loc["gemm_bf16_decode_m16"]
    assert abs(dec["pct_of_roof"] - 134742016 / 47.3e-6 / 3.35e12) < 1e-9
    assert math.isnan(k.loc["bias_add_l2_resident", "pct_of_roof"])
    return "9 kernels classified; precision-specific ceilings; L2-resident anomaly flagged"


def c_mfu(h, a):
    tok_s = 4096 * 1024 / 17.4
    m = a.mfu(tok_s, 70e9, 256, 989e12)
    assert abs(m - 6 * 70e9 * tok_s / (256 * 989e12)) < 1e-12 and 0.39 < m < 0.41, f"MFU {m:.3f}"
    hfu = a.mfu(tok_s, 70e9, 256, 989e12, flops_per_token=8.0)
    assert abs(hfu / m - 8 / 6) < 1e-12
    return f"W-TRAIN MFU {m:.1%}, HFU with full recompute {hfu:.1%}"


CHECKS: list[tuple[str, Callable]] = [
    ("harness.time_samples", c_time_samples), ("harness.summarize_ns", c_summarize_ns),
    ("harness.benches", c_benches), ("harness.manifest_and_suite", c_manifest),
    ("harness.run_independent", c_independent),
    ("analysis.quantile_summary", c_quantile), ("analysis.cliffs_delta", c_cliff),
    ("analysis.clean_runs", c_clean), ("analysis.bootstrap", c_bootstrap),
    ("analysis.permutation_mde", c_permutation), ("analysis.decisions", c_decisions), ("analysis.roofline", c_roofline), ("analysis.mfu", c_mfu),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    h, a = load(args.impl, "harness.py"), load(args.impl, "analysis.py")
    passed = 0
    for name, fn in CHECKS:
        try:
            msg = fn(h, a)
            print(f"PASS {name} — {msg}")
            passed += 1
        except NotImplementedError:
            print(f"TODO {name} — not implemented yet")
        except AssertionError as exc:
            print(f"FAIL {name} — {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {name} — {type(exc).__name__}: {exc}")
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
