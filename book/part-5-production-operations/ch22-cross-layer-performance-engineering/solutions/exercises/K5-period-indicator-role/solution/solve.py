#!/usr/bin/env python3
"""K5 — refit the lab attribution model without the period indicator (`after`).

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


KEY_WITH = {"tp_split": 8.96, "driver_new": 0.90, "storage_new": 1.40}       # exercises-key.md K5
KEY_WITHOUT = {"tp_split": 9.18, "driver_new": 1.07, "storage_new": 1.57}    # exercises-key.md K5
TOL_S = 0.01


def main(out: Path) -> None:
    ft = ref.job_factor_table(ref.load_bundle(DATA))
    full_terms = list(ref.TERMS)
    no_after = [t for t in full_terms if t != "after"]
    c1, s1, r2_1 = ols(ft, full_terms)
    c0, s0, r2_0 = ols(ft, no_after)
    for k, v in KEY_WITH.items():
        assert abs(c1[k] - v) <= TOL_S, (k, c1[k], v)
    for k, v in KEY_WITHOUT.items():
        assert abs(c0[k] - v) <= TOL_S, (k, c0[k], v)
    assert c1["after"] > 3 * s1["after"], "common shift must be real (> 3 SE)"
    rows = [{"term": t, "with_after_s": r(c1[t], 3), "without_after_s": r(c0[t], 3) if t in c0 else None,
             "change_s": r(c0[t] - c1[t], 3) if t in c0 else None} for t in full_terms]
    result = {"id": "K5", "evidence_label": "SIMULATED", "units": "s per step",
              "inputs": {"bundle": "lab/data (seed 2214)", "jobs": int(len(ft)), "terms": full_terms},
              "steps": {"r2_with_after": r(r2_1, 4), "r2_without_after": r(r2_0, 4),
                        "after_coef_s": r(c1["after"], 3), "after_se_s": r(s1["after"], 3), "table": rows},
              "answer": {"driver_new_without_after_s": r(c0["driver_new"], 2),
                         "storage_new_without_after_s": r(c0["storage_new"], 2),
                         "tp_split_without_after_s": r(c0["tp_split"], 2),
                         "alert_node_without_after_s": r(c0["alert_node"], 2)}}
    md = ["# K5 — refit without the period indicator `[SIMULATED]`", "",
          f"Common shift with `after`: {c1['after']:+.2f} ± {s1['after']:.2f} s/step; "
          f"R² {r2_1:.4f} (with) vs {r2_0:.4f} (without).", "",
          "| Term | With `after` (s) | Without (s) |", "|---|---|---|"]
    md += [f"| {x['term']} | {x['with_after_s']:+.3f} | "
           + (f"{x['without_after_s']:+.3f} |" if x["without_after_s"] is not None else "dropped |") for x in rows]
    md += ["", "Without the indicator the common shift is pushed onto the most-exposed factors "
           "(driver +0.17 s, storage +0.17 s, TP +0.22 s) and the ECC alert gains a spurious positive effect."]
    write(out, result, "\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
