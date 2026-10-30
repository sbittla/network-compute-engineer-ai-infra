#!/usr/bin/env python3
"""Chapter 6 lab — reference solution: benchmark statistics, run cleaning, decisions, roofline, MFU.

No scipy: everything is numpy. Latencies in ms; FLOP/s and B/s in SI units; fractions 0..1.

CLI:
    python analysis.py --data ../../lab/data
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
    a = np.sort(np.asarray(x, dtype=float))
    if a.size == 0:
        raise ValueError("empty sample")
    h = (a.size - 1) * q
    lo = int(np.floor(h))
    hi = min(lo + 1, a.size - 1)
    return float(a[lo] + (h - lo) * (a[hi] - a[lo]))


def summarize(x) -> dict:
    """n, mean, median, p5, p95, p99, iqr (p75 − p25), min, max, cv (std/mean, ddof=1)."""
    a = np.asarray(x, dtype=float)
    return {"n": int(a.size), "mean": float(a.mean()), "median": quantile(a, 0.5),
            "p5": quantile(a, 0.05), "p95": quantile(a, 0.95), "p99": quantile(a, 0.99),
            "iqr": quantile(a, 0.75) - quantile(a, 0.25), "min": float(a.min()), "max": float(a.max()),
            "cv": float(a.std(ddof=1) / a.mean()) if a.size > 1 else 0.0}


def cliffs_delta(x, y) -> float:
    """Cliff's delta = P(X > Y) − P(X < Y) over all pairs; −1..1. For latencies, delta(candidate,
    baseline) < 0 means the candidate tends to be faster. |d| < 0.147 negligible, < 0.33 small,
    < 0.474 medium, else large (Romano et al. 2006 conventions)."""
    a = np.asarray(x, dtype=float)[:, None]
    b = np.asarray(y, dtype=float)[None, :]
    return float(((a > b).sum() - (a < b).sum()) / (a.size * b.size))


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
    d = df[df["iter"] >= warmup_iters]
    peer_clock = (float(peer_clock_mhz) if peer_clock_mhz is not None
                  else float(df.groupby("run_id")["sm_clock_mhz"].median().median()))
    excluded = []
    for run_id, g in df.groupby("run_id", sort=True):
        diffs = {k: g[k].iloc[0] for k in ("driver", "cuda", "torch") if str(g[k].iloc[0]) != str(reference_sw[k])}
        if diffs:
            excluded.append({"run_id": run_id, "reason": "version", "detail": f"{diffs} vs reference {reference_sw}"})
            continue
        bad = g[~g["clocks_event_reasons"].isin(ROUTINE_EVENTS)]
        share = len(bad) / len(g)
        med_clk = float(g["sm_clock_mhz"].median())
        if share > event_share_max or med_clk < clock_ratio_min * peer_clock:
            excluded.append({"run_id": run_id, "reason": "clocks",
                             "detail": f"{len(bad)}/{len(g)} iterations with {sorted(set(bad['clocks_event_reasons'])) or '-'}; "
                                       f"median SM clock {med_clk:.0f} MHz vs peer median {peer_clock:.0f} MHz; "
                                       f"max temp {int(g['gpu_temp_c'].max())} C"})
    bad_ids = {e["run_id"] for e in excluded}
    return d[~d["run_id"].isin(bad_ids)].copy(), excluded


def run_medians(df: pd.DataFrame) -> np.ndarray:
    """Median latency per run (the unit of replication), in run_id order."""
    return df.groupby("run_id", sort=True)["latency_ms"].median().to_numpy()


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
    rng = np.random.default_rng(seed)
    nb, nc = len(base_runs), len(cand_runs)
    reps = np.empty(n_boot)
    for i in range(n_boot):
        b = base_runs[rng.integers(0, nb, nb)]
        c = cand_runs[rng.integers(0, nc, nc)]
        reps[i] = np.median(c) / np.median(b) - 1.0
    alpha = (1 - level) / 2
    point = float(np.median(cand_runs) / np.median(base_runs) - 1.0)
    return point, quantile(reps, alpha), quantile(reps, 1 - alpha)


def noise_floor(aa: pd.DataFrame, reference_sw: dict) -> float:
    """A/A noise floor: split bench_aa runs into the two groups by run_id prefix ("AA1-", "AA2-"),
    clean both, and return max(|point|, |lo|, |hi|) of bootstrap_ratio_ci(group1, group2) — the largest
    relative change the measurement process produces when nothing changed."""
    c, _ = clean_runs(aa, reference_sw)
    g1 = run_medians(c[c["run_id"].str.startswith("AA1-")])
    g2 = run_medians(c[c["run_id"].str.startswith("AA2-")])
    p, lo, hi = bootstrap_ratio_ci(g1, g2)
    return float(max(abs(p), abs(lo), abs(hi)))


def permutation_test(base_runs: np.ndarray, cand_runs: np.ndarray) -> float:
    """Exact two-sided permutation test on run medians. Statistic: mean(cand) − mean(base) of the run
    medians (a median-of-medians statistic is too coarse at n = 5: many splits tie with the observed one).
    Enumerate every way to assign the pooled run medians to a 'candidate' group of the same size
    (itertools.combinations over indices); p = (# assignments with |stat| >= |observed| − 1e-12) / total.
    With 5 + 5 runs there are C(10, 5) = 252 assignments, so the smallest possible p is 2/252 ≈ 0.008."""
    pooled = np.concatenate([np.asarray(base_runs, float), np.asarray(cand_runs, float)])
    nc = len(cand_runs)
    obs = abs(np.mean(cand_runs) - np.mean(base_runs))
    count = total = 0
    for idx in itertools.combinations(range(len(pooled)), nc):
        mask = np.zeros(len(pooled), bool)
        mask[list(idx)] = True
        stat = abs(pooled[mask].mean() - pooled[~mask].mean())
        count += stat >= obs - 1e-12
        total += 1
    return count / total


def mde(sigma_run_rel: float, n_runs: int) -> float:
    """Minimum detectable effect (relative) for two arms of n_runs each, two-sided alpha 0.05 and 80 % power:
    MDE ≈ (1.96 + 0.84) × sigma_run × sqrt(2 / n) = 2.8 × sigma_run × sqrt(2 / n), where sigma_run is the
    run-to-run standard deviation of run medians as a fraction of the mean."""
    return 2.8 * sigma_run_rel * math.sqrt(2.0 / n_runs)


def naive_compare(base: pd.DataFrame, cand: pd.DataFrame) -> float:
    """The WRONG way, kept for contrast: mean of every row, no cleaning. Returns mean(cand)/mean(base) − 1."""
    return float(cand["latency_ms"].mean() / base["latency_ms"].mean() - 1.0)


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
    both = pd.concat([base.assign(run_id="base:" + base["run_id"]), cand.assign(run_id="cand:" + cand["run_id"])])
    peer = float(both.groupby("run_id")["sm_clock_mhz"].median().median())  # session-wide peer median
    cb, eb = clean_runs(base, reference_sw, peer_clock_mhz=peer)
    cc, ec = clean_runs(cand, reference_sw, peer_clock_mhz=peer)
    rb, rc = run_medians(cb), run_medians(cc)
    p, lo, hi = bootstrap_ratio_ci(rb, rc)
    pp = permutation_test(rb, rc)
    bar = max(floor, threshold)
    if pp >= ALPHA:
        decision = "not_significant"
    elif abs(p) < bar:
        decision = "below_threshold"
    else:
        decision = "improvement" if p < 0 else "regression"
    return {"point": p, "ci_lo": lo, "ci_hi": hi, "p_perm": pp,
            "cliffs_delta_iter": cliffs_delta(cc["latency_ms"], cb["latency_ms"]),
            "cliffs_delta_runs": cliffs_delta(rc, rb),
            "floor": floor, "threshold": threshold, "decision": decision, "excluded": eb + ec,
            "n_runs_base": int(cb["run_id"].nunique()), "n_runs_cand": int(cc["run_id"].nunique()),
            "naive": naive_compare(base, cand)}


# --------------------------------------------------------------------------------------
# Task 4 — roofline and MFU
# --------------------------------------------------------------------------------------
def ridge_point(peak_flops: float, bw_bytes_per_s: float) -> float:
    """Arithmetic intensity (FLOP/B) where the memory roof meets the compute roof."""
    return peak_flops / bw_bytes_per_s


def attainable(ai: float, peak_flops: float, bw_bytes_per_s: float) -> float:
    """Roofline: min(peak, AI × bandwidth) in FLOP/s."""
    return min(peak_flops, ai * bw_bytes_per_s)


def classify_kernels(kernels: pd.DataFrame, device: dict) -> pd.DataFrame:
    """Add columns: ai (FLOP/B), peak (ceiling for the row's precision), ridge, achieved_flops,
    achieved_bw, bound ("memory" | "compute" | "anomaly"), pct_of_roof, note.

    bound: "anomaly" if achieved_bw > ANOMALY_SLACK × HBM bandwidth or achieved_flops > ANOMALY_SLACK ×
    peak (the counters cannot be right for DRAM — e.g. L2-resident data or miscounted bytes); else
    "memory" if ai < ridge, else "compute". pct_of_roof = achieved_bw / bw for memory-bound,
    achieved_flops / peak for compute-bound, NaN for anomalies.
    """
    bw = float(device["hbm_bytes_per_s"])
    out = kernels.copy()
    rows = []
    for r in out.itertuples(index=False):
        peak = float(device["peak_flops"][r.precision])
        t = float(r.time_us) * 1e-6
        ai = float(r.flop) / float(r.dram_bytes) if r.dram_bytes else float("inf")
        af, ab = float(r.flop) / t, float(r.dram_bytes) / t
        ridge = ridge_point(peak, bw)
        if ab > ANOMALY_SLACK * bw or af > ANOMALY_SLACK * peak:
            bound, pct, note = "anomaly", float("nan"), "exceeds a ceiling: data likely L2-resident or bytes/FLOPs miscounted"
        elif ai < ridge:
            bound, pct, note = "memory", ab / bw, ""
        else:
            bound, pct, note = "compute", af / peak, ""
        rows.append({"ai": ai, "peak": peak, "ridge": ridge, "achieved_flops": af, "achieved_bw": ab,
                     "bound": bound, "pct_of_roof": pct, "note": note})
    return pd.concat([out.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def mfu(tokens_per_s: float, n_params: float, n_gpus: int, peak_flops: float, flops_per_token: float = 6.0) -> float:
    """Model FLOPs utilization = flops_per_token × N × tokens/s ÷ (n_gpus × peak). Use 6 (forward +
    backward) for MFU; 8 for hardware FLOPs utilization (HFU) with full activation recomputation."""
    return flops_per_token * n_params * tokens_per_s / (n_gpus * peak_flops)


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
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
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
