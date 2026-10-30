#!/usr/bin/env python3
"""Chapter 22 lab — attribute a W-TRAIN step-time regression across layers (REFERENCE SOLUTION).

Inputs: the multi-source bundle in ``lab/data/`` (step logs, placement, node inventory, node metrics,
alerts, change log, candidate tests). Output: a per-factor attribution and a before/after report that
separates measured facts, inferred causes, and remaining uncertainty.

All times are seconds per training step. All data are [SIMULATED].

Usage:
    python regression_lab.py --data ../../lab/data --report report.md
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

WARMUP_STEPS = 10
FACTORS = ["after", "tp_split", "driver_new", "storage_new", "alert_node"]
# Model terms: the five factors plus the interaction the dataloader-slack model predicts (Section 22.10.4):
# a TP-split step is ~26 s long, so a marginal loader has slack and storage recalls are mostly hidden.
TERMS = FACTORS + ["tp_x_storage"]
RISK_MULT = {"low": 1.0, "medium": 2.0, "high": 5.0}
LABELS = {"after": "common shift (period indicator; not attributable to a named change)",
          "tp_split": "TP split across nodes (CHG-7790)", "driver_new": "R570 driver, GDR host-staged (CHG-7781)",
          "storage_new": "capacity storage tier (CHG-7795)", "alert_node": "ECC alert node (no change)",
          "tp_x_storage": "interaction: TP split x capacity tier", "residual": "residual"}
N_BOOT = 2000
BOOT_SEED = 22


def load_bundle(data_dir: Path) -> dict:
    """Load every file of the bundle into a dict of DataFrames / parsed YAML (provided, not a TODO)."""
    d = Path(data_dir)
    return {
        "jobs": pd.read_csv(d / "jobs.csv"),
        "steps": pd.read_csv(d / "step_log.csv"),
        "placement": pd.read_csv(d / "placement.csv"),
        "inventory": pd.read_csv(d / "node_inventory.csv"),
        "node_metrics": pd.read_csv(d / "node_metrics.csv"),
        "alerts": pd.read_csv(d / "alerts.csv", keep_default_na=False),
        "changes": yaml.safe_load((d / "change_log.yaml").read_text(encoding="utf-8")),
        "hypotheses": yaml.safe_load((d / "hypotheses.yaml").read_text(encoding="utf-8")),
    }


def clean_steps(steps: pd.DataFrame, warmup_steps: int = WARMUP_STEPS) -> pd.DataFrame:
    """Drop replayed duplicate (job_id, step) rows (keep first) and warm-up steps (step < warmup_steps)."""
    out = steps.drop_duplicates(subset=["job_id", "step"], keep="first")
    out = out[out["step"] >= warmup_steps]
    return out.reset_index(drop=True)


def tp_split_jobs(placement: pd.DataFrame) -> set[int]:
    """Return job IDs where at least one tensor-parallel group spans more than one node."""
    span = placement.groupby(["job_id", "tp_group"])["node"].nunique()
    return {int(j) for j in span[span > 1].index.get_level_values("job_id").unique()}


def job_factor_table(bundle: dict, warmup_steps: int = WARMUP_STEPS) -> pd.DataFrame:
    """One row per job (all jobs, including FAILED ones) with step statistics and factor flags.

    Columns: period, status, n_steps (post-clean), mean_step_s, p50_step_s, p99_step_s,
    mean_data_wait_s, 0/1 factors after, tp_split, driver_new, storage_new, alert_node, and the
    interaction indicator tp_x_storage = tp_split * storage_new.
    driver_new and alert_node are time-aware: a job is exposed only if it ran after the change
    (inventory shows *current* driver state) / after the alert started on a node it used.
    """
    jobs = bundle["jobs"].set_index("job_id")
    st = clean_steps(bundle["steps"], warmup_steps)
    g = st.groupby("job_id")
    ft = pd.DataFrame({
        "n_steps": g.size(),
        "mean_step_s": g["step_time_s"].mean(),
        "p50_step_s": g["step_time_s"].median(),
        "p99_step_s": g["step_time_s"].quantile(0.99),
        "mean_data_wait_s": g["data_wait_s"].mean(),
    })
    ft = jobs[["period", "status", "start_utc", "nodes", "dataset_tier"]].join(ft, how="left")
    new_drv_nodes = set(bundle["inventory"].loc[bundle["inventory"]["driver_branch"] == "R570", "node"])
    split = tp_split_jobs(bundle["placement"])
    alerts = bundle["alerts"]
    ecc = alerts[alerts["alert"] == "NodeGPUCorrectableECCHigh"].iloc[0]
    ecc_node, ecc_start = ecc["target"].split("/")[0], pd.Timestamp(ecc["start_utc"])

    ft["after"] = (ft["period"] == "after").astype(int)
    ft["tp_split"] = ft.index.isin(split).astype(int)
    node_sets = ft["nodes"].str.split(";")
    ft["driver_new"] = [int(a == 1 and bool(set(ns) & new_drv_nodes)) for a, ns in zip(ft["after"], node_sets)]
    ft["storage_new"] = ((ft["dataset_tier"] == "capacity") & (ft["after"] == 1)).astype(int)
    ft["alert_node"] = [int(ecc_node in ns and pd.Timestamp(s) >= ecc_start)
                        for ns, s in zip(node_sets, ft["start_utc"])]
    ft["tp_x_storage"] = ft["tp_split"] * ft["storage_new"]
    return ft.drop(columns=["start_utc", "nodes", "dataset_tier"])



def regression_summary(ft: pd.DataFrame) -> dict:
    """Before/after comparison of per-job mean step time.

    Job-weighted statistics (each job counts once) answer "what did a typical job experience?".
    The step-weighted mean (total seconds / total steps, i.e. GPU-hours per step, since every job uses
    64 GPUs) answers "what did a step cost?" and down-weights short jobs such as the failed one."""
    out = {}
    for period in ("before", "after"):
        d = ft[ft["period"] == period]
        out[f"{period}_mean_s"] = float(d["mean_step_s"].mean())
        out[f"{period}_median_s"] = float(d["mean_step_s"].median())
        out[f"{period}_step_weighted_s"] = float((d["mean_step_s"] * d["n_steps"]).sum() / d["n_steps"].sum())
        out[f"n_{period}"] = int(len(d))
    out["delta_s"] = out["after_mean_s"] - out["before_mean_s"]
    out["delta_pct"] = (out["after_mean_s"] / out["before_mean_s"] - 1) * 100
    out["median_delta_pct"] = (out["after_median_s"] / out["before_median_s"] - 1) * 100
    out["step_weighted_delta_pct"] = (out["after_step_weighted_s"] / out["before_step_weighted_s"] - 1) * 100
    return out


def _design(ft: pd.DataFrame) -> np.ndarray:
    return np.column_stack([np.ones(len(ft))] + [ft[f].to_numpy(float) for f in TERMS])


def estimate_effects(ft: pd.DataFrame) -> dict:
    """OLS of per-job mean step time on an intercept plus TERMS (five factors + tp_x_storage).

    Returns coefficients (s/step), classical (homoskedastic) standard errors ``se``, heteroskedasticity-
    robust HC3 standard errors ``se_hc3`` (residual variance differs a lot between cells: storage-stall
    jobs are far noisier), and R^2."""
    X = _design(ft)
    y = ft["mean_step_s"].to_numpy(float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, p = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(float(resid @ resid) / (n - p) * xtx_inv))
    h = np.einsum("ij,jk,ik->i", X, xtx_inv, X)                    # leverages
    meat = X.T @ (X * (resid / (1 - h))[:, None] ** 2)
    se_hc3 = np.sqrt(np.diag(xtx_inv @ meat @ xtx_inv))
    r2 = 1 - float(resid @ resid) / float(((y - y.mean()) ** 2).sum())
    names = ["intercept"] + TERMS
    return {"coef": dict(zip(names, map(float, beta))), "se": dict(zip(names, map(float, se))),
            "se_hc3": dict(zip(names, map(float, se_hc3))), "r2": r2}


def attribute(ft: pd.DataFrame, effects: dict) -> pd.DataFrame:
    """Contribution of each model term (TERMS) to the before->after change in mean step time.

    contribution_s = coef * (exposure_after - exposure_before); share_pct = contribution / delta * 100.
    Allocation rule: the interaction is reported as its own row (not split between its parents).
    share_se_pp (classical) and share_se_hc3_pp (HC3-robust) = coefficient SE * exposure change / delta
    * 100, treating delta as fixed; the bootstrap (bootstrap_shares) also captures delta's variability.
    A final 'residual' row holds delta minus the sum of contributions."""
    summ = regression_summary(ft)
    rows = []
    for f in TERMS:
        dx = float(ft.loc[ft["period"] == "after", f].mean()) - float(ft.loc[ft["period"] == "before", f].mean())
        c = effects["coef"][f] * dx
        rows.append({"factor": f, "effect_s": effects["coef"][f], "exposure_change": dx, "contribution_s": c,
                     "share_pct": 100 * c / summ["delta_s"],
                     "share_se_pp": 100 * effects["se"][f] * abs(dx) / summ["delta_s"],
                     "share_se_hc3_pp": 100 * effects["se_hc3"][f] * abs(dx) / summ["delta_s"]})
    resid = summ["delta_s"] - sum(r["contribution_s"] for r in rows)
    rows.append({"factor": "residual", "effect_s": np.nan, "exposure_change": np.nan, "contribution_s": resid,
                 "share_pct": 100 * resid / summ["delta_s"], "share_se_pp": np.nan,
                 "share_se_hc3_pp": np.nan})
    return pd.DataFrame(rows).set_index("factor")


def bootstrap_shares(ft: pd.DataFrame, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """Job-level bootstrap of the attribution, resampling jobs with replacement *within each period*
    (24 + 24). Resamples whose design matrix is rank-deficient (e.g. no TP-split x capacity job drawn)
    are discarded and counted. Returns {term: (p2.5, p97.5)} of share_pct, plus 'n_used', 'n_dropped'."""
    rng = np.random.default_rng(seed)
    X_all, y_all = _design(ft), ft["mean_step_s"].to_numpy(float)
    is_after = (ft["period"] == "after").to_numpy()
    idx_b, idx_a = np.flatnonzero(~is_after), np.flatnonzero(is_after)
    draws, dropped = [], 0
    for _ in range(n_boot):
        ib, ia = rng.choice(idx_b, idx_b.size), rng.choice(idx_a, idx_a.size)
        pick = np.concatenate([ib, ia])
        X, y = X_all[pick], y_all[pick]
        if np.linalg.matrix_rank(X) < X.shape[1]:
            dropped += 1
            continue
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        delta = y_all[ia].mean() - y_all[ib].mean()
        dx = X_all[ia, 1:].mean(axis=0) - X_all[ib, 1:].mean(axis=0)
        draws.append(100 * beta[1:] * dx / delta)
    arr = np.array(draws)
    out = {f: (float(np.percentile(arr[:, i], 2.5)), float(np.percentile(arr[:, i], 97.5)))
           for i, f in enumerate(TERMS)}
    out["n_used"], out["n_dropped"] = len(draws), dropped
    return out


def storage_crosscheck(ft: pd.DataFrame, effects: dict) -> dict:
    """Compare the directly measured dataloader-wait delta with the regression's storage coefficient.
    The coefficient is the storage effect for TP-packed jobs (tp_split = 0), so compare like with like:
    after-period, TP-packed jobs, capacity minus hot tier. Agreement within 0.3 s supports the mechanism."""
    a = ft[(ft["period"] == "after") & (ft["tp_split"] == 0)]
    direct = float(a.loc[a["storage_new"] == 1, "mean_data_wait_s"].mean()
                   - a.loc[a["storage_new"] == 0, "mean_data_wait_s"].mean())
    coef = effects["coef"]["storage_new"]
    return {"data_wait_delta_s": direct, "storage_coef_s": coef, "consistent": abs(direct - coef) < 0.3}


def rank_tests(hypotheses: dict) -> tuple[list[dict], list[dict]]:
    """Score = info_value / (cost_hours * risk_multiplier), risk multipliers low=1, medium=2, high=5.
    Tests that are high-risk AND in production are rejected (safety rule), not ranked.
    Returns (ranked tests, highest score first, ties broken by id; rejected tests).
    The ranking is a snapshot: re-score the remaining tests after each result (manuscript 22.3.4)."""
    ranked, rejected = [], []
    for t in hypotheses["tests"]:
        t = dict(t)
        if t["risk"] == "high" and t["environment"] == "production":
            rejected.append(t)
            continue
        t["score"] = t["info_value"] / (t["cost_hours"] * RISK_MULT[t["risk"]])
        ranked.append(t)
    ranked.sort(key=lambda t: (-t["score"], t["id"]))
    return ranked, rejected


def render_report(summary: dict, effects: dict, attribution: pd.DataFrame, cross: dict,
                  ranked: list[dict], rejected: list[dict], boot: dict | None = None,
                  alert_node: str = "orion-n13") -> str:
    """Markdown before/after report with the three mandatory sections."""
    a = attribution
    sh = a["share_pct"]
    lines = [
        "# W-TRAIN sweep regression after CW-2026-10-12 — before/after report",
        "",
        "All values [SIMULATED] (Chapter 22 lab bundle). Job-weighted = mean of per-job post-warm-up means.",
        "",
        "## Measured facts",
        "",
        f"- Mean step time (job-weighted) {summary['before_mean_s']:.2f} s -> {summary['after_mean_s']:.2f} s "
        f"(+{summary['delta_s']:.2f} s, +{summary['delta_pct']:.1f} %), n = {summary['n_before']} / {summary['n_after']} jobs.",
        f"- Median of per-job means {summary['before_median_s']:.2f} s -> {summary['after_median_s']:.2f} s "
        f"(+{summary['median_delta_pct']:.1f} %): the mean is pulled up by a minority of jobs.",
        f"- Step-weighted (GPU-hours per step) {summary['before_step_weighted_s']:.2f} s -> "
        f"{summary['after_step_weighted_s']:.2f} s (+{summary['step_weighted_delta_pct']:.1f} %).",
        f"- Dataloader wait, capacity vs hot tier (after period, TP-packed jobs): +{cross['data_wait_delta_s']:.2f} s/step.",
        "",
        "Allocation rule: each model term is its own row; the TP x storage interaction is NOT split between its",
        "parents. Shares sum to 100 %. Share SEs: classical / HC3-robust.",
        "",
        "| Term | Effect (s/step) ± SE (HC3) | Exposure change | Contribution (s) | Share ± SE (HC3) |",
        "|---|---|---|---|---|",
    ]
    for f, r in a.iterrows():
        eff = "" if np.isnan(r["effect_s"]) else f"{r['effect_s']:+.2f} ± {effects['se'][f]:.2f} ({effects['se_hc3'][f]:.2f})"
        exp = "" if np.isnan(r["exposure_change"]) else f"{r['exposure_change']:.3f}"
        se = "" if np.isnan(r["share_se_pp"]) else f" ± {r['share_se_pp']:.1f} ({r['share_se_hc3_pp']:.1f}) pp"
        lines.append(f"| {LABELS[f]} | {eff} | {exp} | {r['contribution_s']:+.2f} | {r['share_pct']:.1f} %{se} |")
    lines += ["", f"Model R^2 = {effects['r2']:.3f} (OLS on per-job means; intercept + 5 indicators + interaction)."]
    if boot:
        lo, hi = boot["after"]
        lines.append(f"Job-level bootstrap ({boot['n_used']} resamples, {boot['n_dropped']} rank-deficient dropped): "
                     f"future-sweep 95 % interval for the common-shift share {lo:.1f} % to {hi:.1f} % "
                     f"(resamples exposure; for this event use the HC3 share SE).")
    lines += [
        "",
        "## Inferred causes",
        "",
        f"1. TP groups split across two nodes by the new placement policy (CHG-7790): {sh['tp_split']:.1f} %.",
        f"2. Dataset move to the capacity tier (CHG-7795): {sh['storage_new']:.1f} %, with the interaction row "
        f"{sh['tp_x_storage']:+.1f} % (recalls mostly hidden on slow TP-split jobs); the direct data-wait delta agrees "
        f"with the coefficient (consistent={cross['consistent']}).",
        f"3. R570 driver half (CHG-7781): NET channel lines lack /GDRDMA and nvidia_peermem is not loaded, so "
        f"inter-node traffic is host-staged: {sh['driver_new']:.1f} %.",
        f"4. {alert_node} correctable-ECC alert: effect {a.loc['alert_node','effect_s']:+.2f} s "
        f"± {effects['se_hc3']['alert_node']:.2f} — ruled out as a cause.",
        "",
        "## Remaining uncertainty",
        "",
        f"- Common shift (period indicator), not attributable to a named change: {a.loc['after','effect_s']:+.2f} s "
        f"({sh['after']:.1f} % ± {a.loc['after','share_se_pp']:.1f} pp); "
        "candidate: CHG-7802 container rebuild.",
        "- Only the tp_x_storage interaction is modeled; other interactions are assumed zero.",
        "- Causes 1 and 3 are inferred from a natural experiment, not from a controlled A/B.",
        "",
        "## Next discriminating tests (ranked; re-score after each result)",
        "",
    ]
    lines += [f"{i}. {t['id']} ({t['hypothesis']}, score {t['score']:.3f}): {t['action']}" for i, t in enumerate(ranked, 1)]
    lines += ["", "Rejected (high risk in production): " + ", ".join(t["id"] for t in rejected), ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
    ap.add_argument("--report", type=Path, default=None, help="write the Markdown report here")
    args = ap.parse_args()
    b = load_bundle(args.data)
    ft = job_factor_table(b)
    s = regression_summary(ft)
    e = estimate_effects(ft)
    att = attribute(ft, e)
    boot = bootstrap_shares(ft)
    cross = storage_crosscheck(ft, e)
    ranked, rejected = rank_tests(b["hypotheses"])
    ecc_node = b["alerts"].loc[b["alerts"]["alert"] == "NodeGPUCorrectableECCHigh", "target"].iloc[0].split("/")[0]
    rep = render_report(s, e, att, cross, ranked, rejected, boot, ecc_node)
    if args.report:
        args.report.write_text(rep, encoding="utf-8")
    print(rep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
