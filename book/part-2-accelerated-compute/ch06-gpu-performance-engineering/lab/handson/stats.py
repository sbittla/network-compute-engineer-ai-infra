#!/usr/bin/env python3
"""The Chapter 6 statistics (Section 6.7), standard library only.

One pre-registered statistic drives everything: the difference between the arm means of the run medians, as a
percentage of the baseline arm's mean. The point estimate, the 95 % percentile-bootstrap band (resampling runs
within each arm) and the exact two-sided permutation test all use that same statistic. The noise floor is the
largest absolute value an A/A comparison produces (its point and both band bounds). Decision rule, Table 6.6:

  p < 0.05, change < 0, |change| >= max(noise floor, threshold)  -> improvement
  p < 0.05, change > 0, |change| >= max(noise floor, threshold)  -> regression
  p < 0.05, |change| < max(noise floor, threshold)              -> real_but_below_threshold
  p >= 0.05                                                      -> not_significant
"""
from __future__ import annotations

import itertools
import math
import random
import statistics


def change_pct(base: list[float], cand: list[float]) -> float:
    """Primary statistic: (mean(cand run medians) - mean(base run medians)) / mean(base run medians) x 100."""
    return 100.0 * (statistics.mean(cand) - statistics.mean(base)) / statistics.mean(base)


def bootstrap_band(base: list[float], cand: list[float], reps: int = 10_000, seed: int = 6) -> tuple[float, float]:
    """95 % percentile bootstrap of change_pct, resampling runs within each arm. A magnitude band, not a test."""
    rng = random.Random(seed)
    vals = sorted(change_pct([rng.choice(base) for _ in base], [rng.choice(cand) for _ in cand]) for _ in range(reps))
    return vals[int(0.025 * (reps - 1))], vals[int(math.ceil(0.975 * (reps - 1)))]


def permutation_p(base: list[float], cand: list[float]) -> float:
    """Exact two-sided permutation test of the difference in arm means: enumerate every split of the pooled runs.
    (The fixed divisor, mean(base), does not change which splits are at least as extreme, so the difference
    in means is the same test as change_pct with the observed baseline mean as divisor.)"""
    pooled = base + cand
    n, k = len(pooled), len(cand)
    total = sum(pooled)
    obs = abs(statistics.mean(cand) - statistics.mean(base))
    hits = splits = 0
    for idx in itertools.combinations(range(n), k):
        sc = sum(pooled[i] for i in idx)
        diff = sc / k - (total - sc) / (n - k)
        hits += abs(diff) >= obs - 1e-12
        splits += 1
    return hits / splits


def p_floor(n_base: int, n_cand: int) -> float:
    """Smallest two-sided p an exact permutation test can produce: 2 / C(n+m, m)."""
    return 2 / math.comb(n_base + n_cand, n_cand)


def cliffs_delta(x: list[float], y: list[float]) -> float:
    """P(X > Y) - P(X < Y) over all pairs (here over run medians: cand vs base)."""
    gt = sum(1 for a in x for b in y if a > b)
    lt = sum(1 for a in x for b in y if a < b)
    return (gt - lt) / (len(x) * len(y))


def mde_pct(base: list[float], n: int | None = None) -> float:
    """MDE ~ (1.96 + 0.84) * sigma_run * sqrt(2/n), sigma_run = SD of run medians / their mean (Section 6.7)."""
    n = n or len(base)
    sigma = statistics.stdev(base) / statistics.mean(base)
    return 100 * 2.8 * sigma * math.sqrt(2 / n)


def compare(base: list[float], cand: list[float], noise_floor: float, threshold: float) -> dict:
    point = change_pct(base, cand)
    lo, hi = bootstrap_band(base, cand)
    p = permutation_p(base, cand)
    bar = max(noise_floor, threshold)
    if p >= 0.05:
        decision = "not_significant"
    elif abs(point) < bar:
        decision = "real_but_below_threshold"
    else:
        decision = "improvement" if point < 0 else "regression"
    return {"change_pct": point, "band_pct": [lo, hi], "perm_p": p, "p_floor": p_floor(len(base), len(cand)),
            "cliffs_delta_runs": cliffs_delta(cand, base), "decision_bar_pct": bar, "decision": decision,
            "runs": [len(base), len(cand)]}


def noise_floor(aa_1: list[float], aa_2: list[float]) -> dict:
    point = change_pct(aa_1, aa_2)
    lo, hi = bootstrap_band(aa_1, aa_2)
    return {"change_pct": point, "band_pct": [lo, hi], "perm_p": permutation_p(aa_1, aa_2),
            "noise_floor_pct": max(abs(point), abs(lo), abs(hi))}
