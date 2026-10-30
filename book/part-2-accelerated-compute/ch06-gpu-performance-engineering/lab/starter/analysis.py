#!/usr/bin/env python3
"""Chapter 6 lab — STARTER: benchmark statistics, run cleaning, decisions, roofline, MFU.

Implement every function that raises NotImplementedError, then run `python ../check.py`.

No scipy: everything is numpy. Latencies in ms; FLOP/s and B/s in SI units; fractions 0..1.

CLI:
    python analysis.py --data ../data
"""
from __future__ import annotations

import argparse
import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

WARMUP_ITERS = 5
CLOCK_RATIO_MIN = 0.95        # exclude a run whose median SM clock < 95 % of the peer (all-runs) median
EVENT_SHARE_MAX = 0.05        # ... or with throttling events on > 5 % of its iterations
ROUTINE_EVENTS = {"none", "sw_power_cap"}   # power-cap events are routine under heavy GEMMs
PRACTICAL_THRESHOLD = 0.01    # 1 % — smaller changes are not worth shipping for this workload
N_BOOT = 4000
ALPHA = 0.05
ANOMALY_SLACK = 1.02          # achieved > 102 % of a ceiling ⇒ counters or model inconsistent


# --------------------------------------------------------------------------------------
# Task 1 — descriptive statistics
# --------------------------------------------------------------------------------------
def quantile(x, q: float) -> float:
    """Quantile with linear interpolation between order statistics (numpy's default 'linear' method,
    Hyndman & Fan type 7): position h = (n − 1)·q, value = x[⌊h⌋] + (h − ⌊h⌋)(x[⌊h⌋+1] − x[⌊h⌋])."""
    # TODO: sort, compute h = (n-1)*q, interpolate between a[floor(h)] and the next value. Do not call np.quantile.
    raise NotImplementedError("quantile")


def summarize(x) -> dict:
    """n, mean, median, p5, p95, p99, iqr (p75 − p25), min, max, cv (std/mean, ddof=1)."""
    # TODO: use quantile() for every percentile; cv uses the sample standard deviation (ddof=1).
    raise NotImplementedError("summarize")


def cliffs_delta(x, y) -> float:
    """Cliff's delta = P(X > Y) − P(X < Y) over all pairs; −1..1. For latencies, delta(candidate,
    baseline) < 0 means the candidate tends to be faster. |d| < 0.147 negligible, < 0.33 small,
    < 0.474 medium, else large (Romano et al. 2006 conventions)."""
    # TODO: compare every x with every y (numpy broadcasting is fine for a few hundred values).
    raise NotImplementedError("cliffs_delta")


# --------------------------------------------------------------------------------------
# Task 2 — cleaning
# --------------------------------------------------------------------------------------
def clean_runs(df: pd.DataFrame, reference_sw: dict, warmup_iters: int = WARMUP_ITERS,
               event_share_max: float = EVENT_SHARE_MAX, clock_ratio_min: float = CLOCK_RATIO_MIN,
               peer_clock_mhz: float | None = None) -> tuple[pd.DataFrame, list[dict]]:
    """Drop warm-up iterations (iter < warmup_iters) and exclude whole runs that are not comparable.

    Rules are applied in this order, the same way to every arm (pre-registered, symmetric):
      (a) "version": any of driver/cuda/torch differs from reference_sw;
      (b) "clocks": more than event_share_max of the run's iterations report a clocks_event_reasons value
          outside ROUTINE_EVENTS (sw_power_cap is routine and does not count), OR the run's median
          sm_clock_mhz is below clock_ratio_min × peer_clock_mhz. peer_clock_mhz should be the SESSION-WIDE
          peer median (median of per-run median clocks over all runs of all arms being compared; compare()
          passes it); if None, it is computed from df alone. Throttling is judged against peers' sustained
          clock, never max boost.
    Returns (clean iterations, exclusions) where each exclusion is {"run_id", "reason", "detail"}.
    """
    # TODO: drop iter < warmup_iters; compute the peer median clock; exclude whole runs for version first, then clocks.
    raise NotImplementedError("clean_runs")


def run_medians(df: pd.DataFrame) -> np.ndarray:
    """Median latency per run (the unit of replication), in run_id order."""
    # TODO: groupby run_id (sorted), median latency.
    raise NotImplementedError("run_medians")


# --------------------------------------------------------------------------------------
# Task 3 — comparison and decision
# --------------------------------------------------------------------------------------
def bootstrap_ratio_ci(base_runs: np.ndarray, cand_runs: np.ndarray, n_boot: int = N_BOOT, seed: int = 11,
                       level: float = 0.95) -> tuple[float, float, float]:
    """Relative change of candidate vs baseline, (median(cand_runs)/median(base_runs) − 1), with a
    percentile bootstrap CI that resamples RUNS (with replacement) independently in each arm.
    RNG: rng = np.random.default_rng(seed); for each replicate draw baseline indices first
    (rng.integers(0, nb, nb)), then candidate indices (rng.integers(0, nc, nc)).
    Returns (point, lo, hi) as fractions (−0.03 = 3 % faster)."""
    # TODO: follow the RNG recipe in the docstring exactly so results are reproducible.
    raise NotImplementedError("bootstrap_ratio_ci")


def noise_floor(aa: pd.DataFrame, reference_sw: dict) -> float:
    """A/A noise floor: split bench_aa runs into the two groups by run_id prefix ("AA1-", "AA2-"),
    clean both, and return max(|point|, |lo|, |hi|) of bootstrap_ratio_ci(group1, group2) — the largest
    relative change the measurement process produces when nothing changed."""
    # TODO: clean the A/A data, split by prefix, bootstrap, return the largest absolute value.
    raise NotImplementedError("noise_floor")


def permutation_test(base_runs: np.ndarray, cand_runs: np.ndarray) -> float:
    """Exact two-sided permutation test on run medians. Statistic: mean(cand) − mean(base) of the run
    medians (a median-of-medians statistic is too coarse at n = 5: many splits tie with the observed one).
    Enumerate every way to assign the pooled run medians to a 'candidate' group of the same size
    (itertools.combinations over indices); p = (# assignments with |stat| >= |observed| − 1e-12) / total.
    With 5 + 5 runs there are C(10, 5) = 252 assignments, so the smallest possible p is 2/252 ≈ 0.008."""
    # TODO: itertools.combinations over indices of the pooled run medians; count |stat| >= |observed|.
    raise NotImplementedError("permutation_test")


def mde(sigma_run_rel: float, n_runs: int) -> float:
    """Minimum detectable effect (relative) for two arms of n_runs each, two-sided alpha 0.05 and 80 % power:
    MDE ≈ (1.96 + 0.84) × sigma_run × sqrt(2 / n) = 2.8 × sigma_run × sqrt(2 / n), where sigma_run is the
    run-to-run standard deviation of run medians as a fraction of the mean."""
    # TODO: one line.
    raise NotImplementedError("mde")


def naive_compare(base: pd.DataFrame, cand: pd.DataFrame) -> float:
    """The WRONG way, kept for contrast: mean of every row, no cleaning. Returns mean(cand)/mean(base) − 1."""
    # TODO: one line, and then explain in your report why it is wrong.
    raise NotImplementedError("naive_compare")


def compare(base: pd.DataFrame, cand: pd.DataFrame, reference_sw: dict, floor: float,
            threshold: float = PRACTICAL_THRESHOLD) -> dict:
    """Clean both sets with the same rules, compare run medians, and decide.

    Significance comes from the exact permutation test on run medians (p_perm < ALPHA); at 5–6 runs per
    arm a percentile bootstrap CI is not reliable enough to make that call, so the CI is reported as a
    magnitude band only. decision:
      "improvement"     p_perm < ALPHA, point < 0 and |point| ≥ max(floor, threshold)
      "regression"      p_perm < ALPHA, point > 0 and |point| ≥ max(floor, threshold)
      "below_threshold" p_perm < ALPHA but |point| < max(floor, threshold): real but not worth acting on
      "not_significant" p_perm ≥ ALPHA
    Returns point, ci_lo, ci_hi, p_perm (exact permutation test on run medians), cliffs_delta_iter
    (candidate vs baseline, cleaned iterations), cliffs_delta_runs (on run medians), floor, threshold,
    decision, excluded, n_runs_base, n_runs_cand, naive.
    """
    # TODO: clean both with the same rules, permutation test + bootstrap on run medians, apply the decision rules in order.
    raise NotImplementedError("compare")


# --------------------------------------------------------------------------------------
# Task 4 — roofline and MFU
# --------------------------------------------------------------------------------------
def ridge_point(peak_flops: float, bw_bytes_per_s: float) -> float:
    """Arithmetic intensity (FLOP/B) where the memory roof meets the compute roof."""
    # TODO: one line.
    raise NotImplementedError("ridge_point")


def attainable(ai: float, peak_flops: float, bw_bytes_per_s: float) -> float:
    """Roofline: min(peak, AI × bandwidth) in FLOP/s."""
    # TODO: one line.
    raise NotImplementedError("attainable")


def classify_kernels(kernels: pd.DataFrame, device: dict) -> pd.DataFrame:
    """Add columns: ai (FLOP/B), peak (ceiling for the row's precision), ridge, achieved_flops,
    achieved_bw, bound ("memory" | "compute" | "anomaly"), pct_of_roof, note.

    bound: "anomaly" if achieved_bw > ANOMALY_SLACK × HBM bandwidth or achieved_flops > ANOMALY_SLACK ×
    peak (the counters cannot be right for DRAM — e.g. L2-resident data or miscounted bytes); else
    "memory" if ai < ridge, else "compute". pct_of_roof = achieved_bw / bw for memory-bound,
    achieved_flops / peak for compute-bound, NaN for anomalies.
    """
    # TODO: per row: choose the ceiling for its precision, compute AI and achieved rates, check anomalies first.
    raise NotImplementedError("classify_kernels")


def mfu(tokens_per_s: float, n_params: float, n_gpus: int, peak_flops: float, flops_per_token: float = 6.0) -> float:
    """Model FLOPs utilization = flops_per_token × N × tokens/s ÷ (n_gpus × peak). Use 6 (forward +
    backward) for MFU; 8 for hardware FLOPs utilization (HFU) with full activation recomputation."""
    # TODO: one line; see the manuscript Section 6.4 for the 6N vs 8N choice.
    raise NotImplementedError("mfu")


# --------------------------------------------------------------------------------------
# Task 5 — end to end
# --------------------------------------------------------------------------------------
def analyze(data_dir: str | Path) -> dict:
    """Load data, compute the A/A noise floor, compare B and C against the baseline, classify kernels."""
    d = Path(data_dir)
    device = yaml.safe_load((d / "device.yaml").read_text(encoding="utf-8"))
    ref = {"driver": "570.124.06", "cuda": "12.8", "torch": "2.4.0"}
    base = pd.read_csv(d / "bench_baseline.csv", dtype={"cuda": str})
    floor = noise_floor(pd.read_csv(d / "bench_aa.csv", dtype={"cuda": str}), ref)
    res = {"noise_floor": floor}
    for k in ("b", "c"):
        cand = pd.read_csv(d / f"bench_candidate_{k}.csv", dtype={"cuda": str})
        res[f"candidate_{k}"] = compare(base, cand, ref, floor)
    res["kernels"] = classify_kernels(pd.read_csv(d / "kernels.csv"), device)
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = analyze(args.data)
    print(f"A/A noise floor: ±{r['noise_floor']:.2%}")
    for k in ("candidate_b", "candidate_c"):
        c = r[k]
        print(f"{k}: naive {c['naive']:+.2%} | cleaned {c['point']:+.2%} [{c['ci_lo']:+.2%}, {c['ci_hi']:+.2%}] "
              f"p_perm {c['p_perm']:.3f} delta(iter/runs) {c['cliffs_delta_iter']:+.2f}/{c['cliffs_delta_runs']:+.2f} runs {c['n_runs_base']}/{c['n_runs_cand']} -> {c['decision']}")
        for e in c["excluded"]:
            print(f"    excluded {e['run_id']}: {e['reason']} — {e['detail']}")
    cols = ["name", "precision", "ai", "ridge", "bound", "pct_of_roof"]
    print(r["kernels"][cols].to_string(index=False, float_format=lambda v: f"{v:,.3g}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
