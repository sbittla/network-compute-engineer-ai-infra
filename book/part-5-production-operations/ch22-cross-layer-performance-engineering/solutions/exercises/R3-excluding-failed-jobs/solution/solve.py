#!/usr/bin/env python3
"""R3 — lab conclusions with and without the failed job (population rule).

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


FAILED_JOB = 41114
KEY = {"headline_excl_pct": 21.9, "tp_share_excl_pct": 61.4, "after_share_excl_pct": 8.9,
       "headline_all_pct": 23.2, "tp_share_all_pct": 64.7, "after_share_all_pct": 8.3}  # exercises-key.md R3
TOL_PCT = 0.05


def run(ft):
    eff = ref.estimate_effects(ft)
    att = ref.attribute(ft, eff)
    shares = {k: float(att.loc[k, "share_pct"]) for k in ref.TERMS}
    order = [k for k in sorted(("tp_split", "storage_new", "driver_new", "after"), key=lambda k: -shares[k])]
    cross = ref.storage_crosscheck(ft, eff)
    return {"headline_pct": ref.regression_summary(ft)["delta_pct"], "shares": shares, "order": order,
            "alert_effect_s": eff["coef"]["alert_node"], "alert_se_s": eff["se"]["alert_node"],
            "crosscheck_consistent": bool(cross["consistent"]), "data_wait_delta_s": cross["data_wait_delta_s"]}


def main(out: Path) -> None:
    ft = ref.job_factor_table(ref.load_bundle(DATA))
    a, x = run(ft), run(ft[ft.index != FAILED_JOB])
    got = {"headline_all_pct": a["headline_pct"], "headline_excl_pct": x["headline_pct"],
           "tp_share_all_pct": a["shares"]["tp_split"], "tp_share_excl_pct": x["shares"]["tp_split"],
           "after_share_all_pct": a["shares"]["after"], "after_share_excl_pct": x["shares"]["after"]}
    for k, v in KEY.items():
        assert abs(got[k] - v) <= TOL_PCT, (k, got[k], v)
    assert a["order"] == x["order"], "cause ranking must not change"
    for d in (a, x):
        assert abs(d["alert_effect_s"]) < 2 * d["alert_se_s"], "alert verdict must stay 'ruled out'"
        assert d["crosscheck_consistent"]

    def clean(d):
        return {"headline_pct": r(d["headline_pct"], 2), "shares_pct": {k: r(v, 2) for k, v in d["shares"].items()},
                "order": d["order"], "alert_effect_s": r(d["alert_effect_s"], 3), "alert_se_s": r(d["alert_se_s"], 3),
                "crosscheck_consistent": d["crosscheck_consistent"], "data_wait_delta_s": r(d["data_wait_delta_s"], 3)}
    result = {"id": "R3", "evidence_label": "SIMULATED", "units": "%; s",
              "inputs": {"bundle": "lab/data (seed 2214)", "failed_job": FAILED_JOB},
              "steps": {"all_jobs": clean(a), "excluding_failed": clean(x)},
              "answer": {**{k: r(v, 1) for k, v in got.items()}, "ranking_unchanged": True,
                         "alert_verdict_unchanged": True, "crosscheck_unchanged": True}}
    md = ["# R3 — population rule sensitivity `[SIMULATED]`", "",
          "| Quantity | All jobs | Without 41114 |", "|---|---|---|",
          f"| Headline | {a['headline_pct']:+.1f} % | {x['headline_pct']:+.1f} % |"]
    md += [f"| Share: {k} | {a['shares'][k]:.1f} % | {x['shares'][k]:.1f} % |" for k in ref.TERMS]
    md += ["", f"Ranking unchanged: {' > '.join(a['order'])}. Alert effect {x['alert_effect_s']:+.2f} ± "
           f"{x['alert_se_s']:.2f} s (ruled out); storage cross-check consistent in both."]
    write(out, result, "\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
