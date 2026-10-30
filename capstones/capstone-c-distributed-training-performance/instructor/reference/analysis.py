"""Capstone C reference: analysis of supplied W-TRAIN weak-scaling run logs.

INSTRUCTOR EDITION. Same API as starter-kit/starter/analysis.py, fully implemented.
The supplied logs are [SIMULATED]; analysis outputs inherit that label.
"""
from __future__ import annotations

import itertools
import re
from pathlib import Path

import numpy as np
import pandas as pd

ENV_FIELDS = ["container_image", "pytorch", "cuda", "driver", "nccl_version", "nccl_net", "gdr",
              "rdma_dev_in_container", "bucket_cap_mb"]


def load_runs(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (runs, manifests) DataFrames from runs.csv and manifests.csv."""
    d = Path(data_dir)
    runs = pd.read_csv(d / "runs.csv")
    man = pd.read_csv(d / "manifests.csv", keep_default_na=False)
    return runs, man


def steady_state(runs: pd.DataFrame, warmup_steps: int = 5) -> pd.DataFrame:
    """Drop warm-up steps: the first ``warmup_steps`` rows of each run, and the first
    ``warmup_steps`` rows after any restart (a step index lower than the previous one).
    Row order within a run is the log order."""
    keep = []
    for _, g in runs.groupby("run_id", sort=False):
        steps = g["step"].to_numpy()
        since = 0
        mask = np.zeros(len(g), dtype=bool)
        for i in range(len(g)):
            if i > 0 and steps[i] < steps[i - 1]:
                since = 0
            mask[i] = since >= warmup_steps
            since += 1
        keep.append(g[mask])
    return pd.concat(keep).reset_index(drop=True)


def run_summary(steady: pd.DataFrame) -> pd.DataFrame:
    """Per-run statistics of steady-state step time: run_id, variant, n_gpus, rep, n_steps, median_s,
    mean_s, p95_s, iqr_s, cv, tokens_per_step."""
    rows = []
    for rid, g in steady.groupby("run_id", sort=True):
        t = g["step_time_s"].to_numpy()
        q25, q50, q75, q95 = np.percentile(t, [25, 50, 75, 95])
        rows.append({"run_id": rid, "variant": g["variant"].iloc[0], "n_gpus": int(g["n_gpus"].iloc[0]),
                     "rep": int(g["rep"].iloc[0]), "n_steps": int(t.size), "median_s": float(q50),
                     "mean_s": float(t.mean()), "p95_s": float(q95), "iqr_s": float(q75 - q25),
                     "cv": float(t.std(ddof=1) / t.mean()), "tokens_per_step": int(g["tokens"].iloc[0])})
    return pd.DataFrame(rows)


def validate_runs(runs: pd.DataFrame, manifests: pd.DataFrame, summary: pd.DataFrame,
                  outlier_floor: float = 0.02) -> pd.DataFrame:
    """Decide which runs are admissible. Columns: run_id, variant, n_gpus, rep, valid, reasons.

    Reasons (';'-joined):
      * restarted — the log has a repeated step index (job resumed from a checkpoint mid-run);
      * env_mismatch:<field> — an ENV_FIELDS value differs from the modal value of that variant;
      * outlier — the run's median deviates from its (variant, n_gpus) group median by more than
        max(3 × 1.4826 × MAD, outlier_floor × group median).
    """
    restarted = {rid for rid, g in runs.groupby("run_id") if g["step"].duplicated().any()}
    reasons: dict[str, list[str]] = {rid: [] for rid in manifests["run_id"]}
    for rid in restarted:
        reasons[rid].append("restarted")
    for var, g in manifests.groupby("variant"):
        for f in ENV_FIELDS:
            mode = g[f].astype(str).mode().iloc[0]
            for rid in g.loc[g[f].astype(str) != mode, "run_id"]:
                reasons[rid].append(f"env_mismatch:{f}")
    for _, g in summary.groupby(["variant", "n_gpus"]):
        med = g["median_s"].median()
        mad = (g["median_s"] - med).abs().median()
        lim = max(3 * 1.4826 * mad, outlier_floor * med)
        for rid in g.loc[(g["median_s"] - med).abs() > lim, "run_id"]:
            reasons[rid].append("outlier")
    rows = []
    for m in manifests.itertuples(index=False):
        rs = reasons[m.run_id]
        rows.append({"run_id": m.run_id, "variant": m.variant, "n_gpus": int(m.n_gpus), "rep": int(m.rep),
                     "valid": not rs, "reasons": ";".join(rs)})
    return pd.DataFrame(rows)


def scaling_table(summary: pd.DataFrame, validation: pd.DataFrame, base_gpus: int = 32) -> pd.DataFrame:
    """Weak-scaling table over valid runs, per (variant, n_gpus): n_runs, median_step_s (median of run
    medians), min_step_s, max_step_s, tokens_per_s, tokens_per_s_per_gpu, weak_scaling_eff
    (per-GPU throughput relative to the same variant at ``base_gpus``)."""
    ok = summary.merge(validation[["run_id", "valid"]], on="run_id")
    ok = ok[ok["valid"]]
    rows = []
    for (var, n), g in ok.groupby(["variant", "n_gpus"]):
        med = float(g["median_s"].median())
        tps = g["tokens_per_step"].iloc[0] / med
        rows.append({"variant": var, "n_gpus": int(n), "n_runs": int(len(g)), "median_step_s": med,
                     "min_step_s": float(g["median_s"].min()), "max_step_s": float(g["median_s"].max()),
                     "tokens_per_s": tps, "tokens_per_s_per_gpu": tps / n})
    t = pd.DataFrame(rows)
    base = t[t["n_gpus"] == base_gpus].set_index("variant")["tokens_per_s_per_gpu"]
    t["weak_scaling_eff"] = t["tokens_per_s_per_gpu"] / t["variant"].map(base)
    return t.sort_values(["variant", "n_gpus"]).reset_index(drop=True)


def permutation_pvalue(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    """Exact two-sided permutation test. Statistic: the difference of means of the two groups (here, of
    run medians). Enumerates all C(n_a+n_b, n_a) relabellings; p = fraction with |diff| ≥ observed |diff|."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    pooled = np.concatenate([a, b])
    n, k = pooled.size, a.size
    obs = abs(a.mean() - b.mean())
    combs = np.array(list(itertools.combinations(range(n), k)), dtype=int)
    sum_a = pooled[combs].sum(axis=1)
    diff = np.abs(sum_a / k - (pooled.sum() - sum_a) / (n - k))
    return float(np.mean(diff >= obs - 1e-12))


def holm(pvals: list[float]) -> list[float]:
    """Holm–Bonferroni step-down adjusted p-values (same order as the input), capped at 1."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def compare_variants(summary: pd.DataFrame, validation: pd.DataFrame, a: str, b: str,
                     n_boot: int = 2000, seed: int = 0, alpha: float = 0.05) -> pd.DataFrame:
    """Compare variant ``b`` against ``a`` at each scale using valid runs' medians.

    Columns: comparison, n_gpus, n_a, n_b, median_a_s, median_b_s, speedup (median_a / median_b; > 1 means b
    is faster), p_value (raw exact permutation p on the difference of means of run medians), ci_low,
    ci_high (percentile bootstrap of the speedup, resampling runs within each variant,
    ``np.random.default_rng(seed)``). Significance is decided across the whole family of comparisons by
    ``compare_family`` (Holm correction).
    """
    ok = summary.merge(validation[["run_id", "valid"]], on="run_id")
    ok = ok[ok["valid"]]
    rng = np.random.default_rng(seed)
    rows = []
    for n in sorted(set(ok["n_gpus"])):
        xa = ok[(ok["variant"] == a) & (ok["n_gpus"] == n)]["median_s"].to_numpy()
        xb = ok[(ok["variant"] == b) & (ok["n_gpus"] == n)]["median_s"].to_numpy()
        if xa.size == 0 or xb.size == 0:
            continue
        sp = np.median(xa) / np.median(xb)
        boots = np.array([np.median(rng.choice(xa, xa.size)) / np.median(rng.choice(xb, xb.size))
                          for _ in range(n_boot)])
        lo, hi = np.percentile(boots, [2.5, 97.5])
        rows.append({"comparison": f"{a}->{b}", "n_gpus": int(n), "n_a": int(xa.size), "n_b": int(xb.size),
                     "median_a_s": float(np.median(xa)), "median_b_s": float(np.median(xb)), "speedup": float(sp),
                     "p_value": permutation_pvalue(xa, xb), "ci_low": float(lo), "ci_high": float(hi)})
    return pd.DataFrame(rows)


def compare_family(summary: pd.DataFrame, validation: pd.DataFrame, pairs: list[tuple[str, str]],
                   alpha: float = 0.05, seed: int = 0) -> pd.DataFrame:
    """Run compare_variants for every (a, b) pair, then Holm-adjust the p-values across the whole family
    (e.g. 2 comparisons × 4 scales = 8 tests). Adds p_holm and significant (p_holm < alpha AND the
    bootstrap CI excludes 1.0)."""
    t = pd.concat([compare_variants(summary, validation, a, b, seed=seed) for a, b in pairs], ignore_index=True)
    t["p_holm"] = holm(t["p_value"].tolist())
    t["significant"] = (t["p_holm"] < alpha) & ((t["ci_low"] > 1.0) | (t["ci_high"] < 1.0))
    return t


def exposed_comm(profile: pd.DataFrame) -> pd.DataFrame:
    """From profile_summary.csv (milliseconds): per (variant, n_gpus) step_ms (sum of exposed_ms over
    all categories), comm_busy_ms and comm_exposed_ms (categories starting 'nccl_'),
    exposed_comm_fraction (comm_exposed_ms / step_ms), memcpy_busy_ms."""
    rows = []
    for (v, n), g in profile.groupby(["variant", "n_gpus"]):
        comm = g[g["category"].str.startswith("nccl_")]
        step = g["exposed_ms"].sum()
        rows.append({"variant": v, "n_gpus": int(n), "step_ms": float(step),
                     "comm_busy_ms": float(comm["busy_ms"].sum()), "comm_exposed_ms": float(comm["exposed_ms"].sum()),
                     "exposed_comm_fraction": float(comm["exposed_ms"].sum() / step),
                     "memcpy_busy_ms": float(g.loc[g["category"].str.startswith("memcpy"), "busy_ms"].sum())})
    return pd.DataFrame(rows)


def nccl_transport(log_text: str) -> dict[str, object]:
    """Parse an NCCL_DEBUG=INFO excerpt: network ('IB' | 'Socket' | 'unknown' from 'Using network X'),
    gdr (True if any channel line shows '/GDRDMA'), ib_devices (list like ['mlx5_0', ...]),
    no_ib_device (True if 'NET/IB : No device found.' appears)."""
    m = re.search(r"Using network (\w+)", log_text)
    devs = re.findall(r"\[\d+\](mlx5_\d+):\d+/", log_text)
    return {"network": m.group(1) if m else "unknown", "gdr": "/GDRDMA" in log_text,
            "ib_devices": sorted(set(devs), key=lambda s: int(s.split("_")[1])),
            "no_ib_device": "NET/IB : No device found." in log_text}
