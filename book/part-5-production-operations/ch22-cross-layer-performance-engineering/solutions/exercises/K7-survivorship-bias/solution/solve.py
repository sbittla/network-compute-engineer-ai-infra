#!/usr/bin/env python3
"""K7 — effect of dropping the failed TP-split job (survivorship bias) on the lab attribution.

Usage: python solve.py --out DIR   (writes result.json and result.md; asserts the answer key)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def r(x: float, nd: int = 4) -> float:
    return round(float(x), nd)


def write(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    (out / "result.md").write_text(md.rstrip() + "\n", encoding="utf-8")


# Lab bundle and reference implementation of this package (instructor image only).
PKG = Path(__file__).resolve().parents[4]
DATA = PKG / "lab" / "data"
sys.path.insert(0, str(PKG / "solutions" / "lab"))
import numpy as np  # noqa: E402
import regression_lab as ref  # noqa: E402


def ols(ft, terms):
    """OLS of per-job mean step time on an intercept plus `terms`; returns coef, classical SE, R^2."""
    X = np.column_stack([np.ones(len(ft))] + [ft[t].to_numpy(float) for t in terms])
    y = ft["mean_step_s"].to_numpy(float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    n, p = X.shape
    se = np.sqrt(np.diag(float(res @ res) / (n - p) * np.linalg.inv(X.T @ X)))
    r2 = 1 - float(res @ res) / float(((y - y.mean()) ** 2).sum())
    names = ["intercept"] + list(terms)
    return dict(zip(names, map(float, beta))), dict(zip(names, map(float, se))), r2


FAILED_JOB = 41114                       # jobs.csv: status FAILED, TP-split, NCCL timeout
KEY = {"headline_all_pct": 23.2, "headline_excl_pct": 21.9,      # exercises-key.md K7 / lab key
       "tp_share_all_pct": 64.7, "tp_share_excl_pct": 61.4}
TOL_PCT = 0.05


def main(out: Path) -> None:
    bundle = ref.load_bundle(DATA)
    ft = ref.job_factor_table(bundle)
    assert ft.loc[FAILED_JOB, "status"] == "FAILED" and int(ft.loc[FAILED_JOB, "tp_split"]) == 1
    res = {}
    for name, d in (("all", ft), ("excl", ft[ft.index != FAILED_JOB])):
        s = ref.regression_summary(d)
        a = ref.attribute(d, ref.estimate_effects(d))
        res[name] = {"headline_pct": s["delta_pct"], "tp_share_pct": float(a.loc["tp_split", "share_pct"]),
                     "after_share_pct": float(a.loc["after", "share_pct"]), "n_jobs": int(len(d))}
    got = {"headline_all_pct": res["all"]["headline_pct"], "headline_excl_pct": res["excl"]["headline_pct"],
           "tp_share_all_pct": res["all"]["tp_share_pct"], "tp_share_excl_pct": res["excl"]["tp_share_pct"]}
    for k, v in KEY.items():
        assert abs(got[k] - v) <= TOL_PCT, (k, got[k], v)
    result = {"id": "K7", "evidence_label": "SIMULATED", "units": "%",
              "inputs": {"bundle": "lab/data (seed 2214)", "failed_job": FAILED_JOB,
                         "failed_job_usable_steps": int(ft.loc[FAILED_JOB, "n_steps"])},
              "steps": {k: {kk: (r(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                        for k, v in res.items()},
              "answer": {k: r(v, 1) for k, v in got.items()}}
    md = ["# K7 — survivorship bias in the lab `[SIMULATED]`", "",
          "| Population | Jobs | Headline | TP share | Common-shift share |", "|---|---|---|---|---|"]
    for k, lab in (("all", "All jobs"), ("excl", f"Excluding failed {FAILED_JOB}")):
        v = res[k]
        md.append(f"| {lab} | {v['n_jobs']} | {v['headline_pct']:+.1f} % | {v['tp_share_pct']:.1f} % | "
                  f"{v['after_share_pct']:.1f} % |")
    md += ["", "Dropping the failed TP-split job shrinks the headline and the share of the very factor that "
           "caused the failure."]
    write(out, result, "\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
