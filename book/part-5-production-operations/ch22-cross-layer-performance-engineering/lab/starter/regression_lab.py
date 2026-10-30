#!/usr/bin/env python3
"""Chapter 22 lab — attribute a W-TRAIN step-time regression across layers (STARTER — complete the TODOs).

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
    """Return a clean step log: at most one row per (job_id, step) (keep the first) and no warm-up
    steps (step < warmup_steps)."""
    # TODO: enforce uniqueness on (job_id, step), then drop warm-up steps. Print how many rows each
    #       rule removed: if either number surprises you, find out why before trusting any mean.
    raise NotImplementedError("clean_steps")


def tp_split_jobs(placement: pd.DataFrame) -> set[int]:
    """Return job IDs where at least one tensor-parallel group spans more than one node."""
    # TODO: group placement by (job_id, tp_group) and count distinct nodes; a TP group on >1 node
    #       means its TP all-reduce leaves NVLink.
    raise NotImplementedError("tp_split_jobs")


def job_factor_table(bundle: dict, warmup_steps: int = WARMUP_STEPS) -> pd.DataFrame:
    """One row per job listed in jobs.csv (every job, whatever its status) with step statistics and
    factor flags.

    Columns: period, status, n_steps (post-clean), mean_step_s, p50_step_s, p99_step_s,
    mean_data_wait_s, 0/1 factors after, tp_split, driver_new, storage_new, alert_node, and the
    interaction indicator tp_x_storage = tp_split * storage_new.
    driver_new and alert_node are time-aware: a job is exposed only if it ran after the change
    (inventory shows *current* driver state) / after the alert started on a node it used.
    """
    # TODO: per-job stats from clean_steps(); join jobs.csv; derive the 0/1 factors and tp_x_storage.
    #       Ask of every join: was this attribute true *when the job ran*?
    raise NotImplementedError("job_factor_table")


def regression_summary(ft: pd.DataFrame) -> dict:
    """Before/after comparison of per-job mean step time.

    Job-weighted statistics (each job counts once) answer "what did a typical job experience?".
    The step-weighted mean (total seconds / total steps, i.e. GPU-hours per step, since every job uses
    64 GPUs) answers "what did a step cost?" and down-weights short jobs such as the failed one."""
    # TODO: per period: job-weighted mean and median of mean_step_s, step-weighted mean, n;
    #       then delta_s, delta_pct, median_delta_pct, step_weighted_delta_pct.
    raise NotImplementedError("regression_summary")


def _design(ft: pd.DataFrame) -> np.ndarray:
    return np.column_stack([np.ones(len(ft))] + [ft[f].to_numpy(float) for f in TERMS])


def estimate_effects(ft: pd.DataFrame) -> dict:
    """OLS of per-job mean step time on an intercept plus TERMS (five factors + tp_x_storage).

    Returns coefficients (s/step), classical (homoskedastic) standard errors ``se``, heteroskedasticity-
    robust HC3 standard errors ``se_hc3`` (residual variance differs a lot between cells: storage-stall
    jobs are far noisier), and R^2."""
    # TODO: OLS (numpy.linalg.lstsq) of mean_step_s on _design(ft); return coef, se (classical:
    #       sqrt diag of RSS/(n-p) * (X'X)^-1), se_hc3 ((X'X)^-1 X' diag(e_i^2/(1-h_i)^2) X (X'X)^-1), r2.
    raise NotImplementedError("estimate_effects")


def attribute(ft: pd.DataFrame, effects: dict) -> pd.DataFrame:
    """Contribution of each model term (TERMS) to the before->after change in mean step time.

    contribution_s = coef * (exposure_after - exposure_before); share_pct = contribution / delta * 100.
    Allocation rule: the interaction is reported as its own row (not split between its parents).
    share_se_pp (classical) and share_se_hc3_pp (HC3-robust) = coefficient SE * exposure change / delta
    * 100, treating delta as fixed; the bootstrap (bootstrap_shares) also captures delta's variability.
    A final 'residual' row holds delta minus the sum of contributions."""
    # TODO: contribution = coef * (exposure_after - exposure_before); share = contribution / delta * 100;
    #       share_se_pp / share_se_hc3_pp from the two SEs; add a 'residual' row.
    raise NotImplementedError("attribute")


def bootstrap_shares(ft: pd.DataFrame, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """Job-level bootstrap of the attribution, resampling jobs with replacement *within each period*
    (24 + 24). Resamples whose design matrix is rank-deficient (e.g. no TP-split x capacity job drawn)
    are discarded and counted. Returns {term: (p2.5, p97.5)} of share_pct, plus 'n_used', 'n_dropped'."""
    # TODO: resample jobs with replacement within each period; skip rank-deficient designs (count them);
    #       refit, recompute delta and exposure changes, collect shares; return 2.5/97.5 percentiles.
    raise NotImplementedError("bootstrap_shares")


def storage_crosscheck(ft: pd.DataFrame, effects: dict) -> dict:
    """Compare the directly measured dataloader-wait delta with the regression's storage coefficient.
    The coefficient is the storage effect for TP-packed jobs (tp_split = 0), so compare like with like:
    after-period, TP-packed jobs, capacity minus hot tier. Agreement within 0.3 s supports the mechanism."""
    # TODO: after-period TP-packed jobs: mean data_wait_s (capacity minus hot) vs the storage_new
    #       coefficient; consistent if |difference| < 0.3 s.
    raise NotImplementedError("storage_crosscheck")


def rank_tests(hypotheses: dict) -> tuple[list[dict], list[dict]]:
    """Score = info_value / (cost_hours * risk_multiplier), risk multipliers low=1, medium=2, high=5.
    Tests that are high-risk AND in production are rejected (safety rule), not ranked.
    Returns (ranked tests, highest score first, ties broken by id; rejected tests).
    The ranking is a snapshot: re-score the remaining tests after each result (manuscript 22.3.4)."""
    # TODO: score = info_value / (cost_hours * RISK_MULT[risk]); reject high-risk production tests;
    #       sort by -score then id.
    raise NotImplementedError("rank_tests")


def render_report(summary: dict, effects: dict, attribution: pd.DataFrame, cross: dict,
                  ranked: list[dict], rejected: list[dict], boot: dict | None = None,
                  alert_node: str = "orion-n13") -> str:
    """Markdown before/after report with the three mandatory sections."""
    # TODO: Markdown with '## Measured facts', '## Inferred causes', '## Remaining uncertainty' (in that
    #       order), the headline % change, the full term table, the alert verdict, and the ranked tests.
    raise NotImplementedError("render_report")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[1] / "data")
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
