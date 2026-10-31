#!/usr/bin/env python3
"""W1 — attribution with an interaction (cell means, exposures, contributions).

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


BEFORE_MEAN_S = 17.40                                     # prompt: 10 before-period jobs
CELLS = {(0, 0): (4, 17.6), (1, 0): (3, 24.8), (0, 1): (2, 19.4), (1, 1): (1, 28.2)}  # (P,S): (jobs, mean s)
KEY = {"after_mean_s": 21.18, "delta_s": 3.78, "delta_pct": 21.7, "period_s": 0.20, "P_s": 7.20, "S_s": 1.80,
       "PxS_s": 1.60, "naive_P_s": 7.45, "naive_S_s": 1.65,
       "share_pct": {"period": 5.3, "P": 76.2, "S": 14.3, "PxS": 4.2}}   # exercises-key.md W1
TOL = 0.005


def main(out: Path) -> None:
    n = sum(j for j, _ in CELLS.values())
    after = sum(j * m for j, m in CELLS.values()) / n
    delta = after - BEFORE_MEAN_S
    m = {k: v[1] for k, v in CELLS.items()}
    eff = {"period": m[(0, 0)] - BEFORE_MEAN_S, "P": m[(1, 0)] - m[(0, 0)], "S": m[(0, 1)] - m[(0, 0)]}
    eff["PxS"] = m[(1, 1)] - m[(0, 0)] - eff["P"] - eff["S"]
    expo = {"period": 1.0,
            "P": sum(j for (p, _), (j, _) in CELLS.items() if p) / n,
            "S": sum(j for (_, s), (j, _) in CELLS.items() if s) / n,
            "PxS": CELLS[(1, 1)][0] / n}
    contrib = {k: eff[k] * expo[k] for k in eff}
    share = {k: 100 * contrib[k] / delta for k in eff}
    assert abs(sum(contrib.values()) - delta) < 1e-9, "attribution must balance"

    def cmean(sel):
        js = [(j, mm) for k, (j, mm) in CELLS.items() if sel(k)]
        return sum(j * mm for j, mm in js) / sum(j for j, _ in js)
    naive_p = cmean(lambda k: k[0] == 1) - cmean(lambda k: k[0] == 0)
    naive_s = cmean(lambda k: k[1] == 1) - cmean(lambda k: k[1] == 0)

    got = {"after_mean_s": after, "delta_s": delta, "delta_pct": 100 * delta / BEFORE_MEAN_S,
           "period_s": eff["period"], "P_s": eff["P"], "S_s": eff["S"], "PxS_s": eff["PxS"],
           "naive_P_s": naive_p, "naive_S_s": naive_s}
    for k, v in KEY.items():
        if k == "share_pct":
            for t, sv in v.items():
                assert abs(share[t] - sv) <= 0.05, (t, share[t], sv)
        else:
            tol = 0.05 if k == "delta_pct" else TOL
            assert abs(got[k] - v) <= tol, (k, got[k], v)
    rows = [{"term": t, "effect_s": r(eff[t], 3), "exposure_change": r(expo[t], 3),
             "contribution_s": r(contrib[t], 3), "share_pct": r(share[t], 2)} for t in ("period", "P", "S", "PxS")]
    result = {"id": "W1", "evidence_label": "ILLUSTRATIVE", "units": "s per step; %",
              "inputs": {"before_mean_s": BEFORE_MEAN_S,
                         "cells": [{"P": p, "S": s, "jobs": j, "mean_s": mm} for (p, s), (j, mm) in CELLS.items()]},
              "steps": {"attribution": rows, "mean_P1_s": r(cmean(lambda k: k[0] == 1), 3),
                        "mean_P0_s": r(cmean(lambda k: k[0] == 0), 3), "mean_S1_s": r(cmean(lambda k: k[1] == 1), 3),
                        "mean_S0_s": r(cmean(lambda k: k[1] == 0), 3)},
              "answer": {k: r(v, 3) for k, v in got.items()}}
    md = ["# W1 — attribution with an interaction `[ILLUSTRATIVE]`", "",
          f"After mean {after:.2f} s; Δ {delta:.2f} s ({100 * delta / BEFORE_MEAN_S:+.1f} %).", "",
          "| Term | Effect (s) | Δ exposure | Contribution (s) | Share |", "|---|---|---|---|---|"]
    md += [f"| {x['term']} | {x['effect_s']:.2f} | {x['exposure_change']:.1f} | {x['contribution_s']:.2f} | "
           f"{x['share_pct']:.1f} % |" for x in rows]
    md += [f"| Total | | | {sum(contrib.values()):.2f} | 100 % |", "",
           f"Naive within-after differences: P {naive_p:.2f} s, S {naive_s:.2f} s (biased by the unbalanced mix "
           "and the interaction)."]
    write(out, result, "\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
