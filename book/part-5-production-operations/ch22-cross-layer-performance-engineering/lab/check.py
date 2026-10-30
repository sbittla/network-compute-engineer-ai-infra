#!/usr/bin/env python3
"""Checker for the Chapter 22 lab (regression attribution).

    python check.py                    # checks starter/regression_lab.py (default)
    python check.py --impl solution    # checks ../solutions/lab/regression_lab.py

Prints one PASS/FAIL/TODO line per check. Exit 0 only if every check passes. Pure Python, no hardware,
no network; runs in a few seconds. Expected values come from the seeded bundle in data/ ([SIMULATED]).
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMPLS = {"starter": HERE / "starter" / "regression_lab.py",
         "solution": HERE.parent / "solutions" / "lab" / "regression_lab.py"}

EXPECTED_CLEAN_ROWS = 8990
EXPECTED_TP_SPLIT = {41102, 41107, 41109, 41112, 41114, 41117, 41123}
EXPECTED_FACTOR_COUNTS = {"after": 24, "tp_split": 7, "driver_new": 12, "storage_new": 14, "alert_node": 6,
                          "tp_x_storage": 3}
# (expected, tolerance) — values from the reference analysis of the committed bundle
EXPECTED_EFFECTS = {"tp_split": (8.96, 0.25), "driver_new": (0.90, 0.20), "storage_new": (1.40, 0.20),
                    "after": (0.34, 0.20), "alert_node": (0.0, 0.25), "tp_x_storage": (-1.31, 0.30)}
EXPECTED_SHARES = {"tp_split": (64.6, 3.0), "storage_new": (20.0, 3.0), "driver_new": (11.2, 3.0),
                   "tp_x_storage": (-4.1, 2.0)}
EXPECTED_RANK = ["T3", "T1", "T2", "T4", "T8", "T6", "T7"]
EXPECTED_REJECTED = {"T5", "T9"}


def load(impl: str):
    path = IMPLS[impl]
    spec = importlib.util.spec_from_file_location(f"regression_lab_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(mod)
    return mod


class Ctx:
    """Lazily computed intermediate results shared between checks."""

    def __init__(self, mod):
        self.m = mod
        self._c: dict = {}

    def get(self, key: str):
        if key not in self._c:
            m = self.m
            if key == "bundle":
                v = m.load_bundle(DATA)
            elif key == "ft":
                v = m.job_factor_table(self.get("bundle"))
            elif key == "summary":
                v = m.regression_summary(self.get("ft"))
            elif key == "effects":
                v = m.estimate_effects(self.get("ft"))
            elif key == "attr":
                v = m.attribute(self.get("ft"), self.get("effects"))
            elif key == "cross":
                v = m.storage_crosscheck(self.get("ft"), self.get("effects"))
            elif key == "boot":
                v = m.bootstrap_shares(self.get("ft"))
            elif key == "rank":
                v = m.rank_tests(self.get("bundle")["hypotheses"])
            else:
                raise KeyError(key)
            self._c[key] = v
        return self._c[key]


def near(x: float, target: float, tol: float) -> bool:
    return x is not None and not math.isnan(x) and abs(x - target) <= tol


def c_clean(ctx):
    b = ctx.get("bundle")
    out = ctx.m.clean_steps(b["steps"])
    n = len(out)
    dup = out.duplicated(subset=["job_id", "step"]).sum()
    ok = n == EXPECTED_CLEAN_ROWS and dup == 0 and out["step"].min() >= 10
    return ok, f"{n} rows after cleaning (expected {EXPECTED_CLEAN_ROWS}), {dup} duplicate job-steps, min step {out['step'].min()}"


def c_tp(ctx):
    got = set(ctx.m.tp_split_jobs(ctx.get("bundle")["placement"]))
    return got == EXPECTED_TP_SPLIT, f"{len(got)} TP-split jobs found; missing {sorted(EXPECTED_TP_SPLIT - got)}, extra {sorted(got - EXPECTED_TP_SPLIT)}"


def c_factors(ctx):
    ft = ctx.get("ft")
    if len(ft) != 48:
        return False, f"{len(ft)} job rows (expected 48: every job in jobs.csv)"
    counts = {f: int(ft[f].sum()) for f in EXPECTED_FACTOR_COUNTS}
    bad = {f: (counts[f], e) for f, e in EXPECTED_FACTOR_COUNTS.items() if counts[f] != e}
    return not bad, "factor exposure counts match" if not bad else f"mismatched (got, expected): {bad}"


def c_failed(ctx):
    ft = ctx.get("ft")
    n = int(ft.loc[41114, "n_steps"]) if 41114 in ft.index and not math.isnan(ft.loc[41114, "n_steps"]) else 0
    return n == 60, f"job 41114 has {n} usable steps (expected 60)"


def c_summary(ctx):
    s = ctx.get("summary")
    ok = (near(s["delta_pct"], 23.2, 0.3) and near(s["median_delta_pct"], 13.1, 0.5)
          and near(s["before_mean_s"], 17.38, 0.05) and near(s["step_weighted_delta_pct"], 22.3, 0.3))
    return ok, (f"before {s['before_mean_s']:.2f} s, after {s['after_mean_s']:.2f} s, mean +{s['delta_pct']:.1f} % (exp 23.2), "
                f"median +{s['median_delta_pct']:.1f} % (exp 13.1), step-weighted +{s['step_weighted_delta_pct']:.1f} % (exp 22.3)")


def c_effects(ctx):
    coef = ctx.get("effects")["coef"]
    bad = {f: round(coef.get(f, float("nan")), 2) for f, (e, t) in EXPECTED_EFFECTS.items() if not near(coef.get(f), e, t)}
    return not bad, "all six model terms within tolerance" if not bad else f"out of tolerance: {bad} expected {EXPECTED_EFFECTS}"


def c_attr(ctx):
    a = ctx.get("attr")
    s = ctx.get("summary")
    tot = float(a["contribution_s"].sum())
    bad = {f: round(float(a.loc[f, "share_pct"]), 1) for f, (e, t) in EXPECTED_SHARES.items() if not near(float(a.loc[f, "share_pct"]), e, t)}
    se_ok = near(float(a.loc["after", "share_se_pp"]), 2.2, 0.3) and near(float(a.loc["tp_split", "share_se_pp"]), 0.7, 0.2)
    hc3_ok = "share_se_hc3_pp" in a.columns and near(float(a.loc["after", "share_se_hc3_pp"]), 1.7, 0.3)
    ok = not bad and near(tot, s["delta_s"], 0.01) and abs(float(a.loc["residual", "share_pct"])) < 1.0 and se_ok and hc3_ok
    return ok, (f"contributions sum {tot:.2f} s vs delta {s['delta_s']:.2f} s; share issues {bad or 'none'}; "
                f"share SE ok={se_ok}, HC3 ok={hc3_ok}")


def c_boot(ctx):
    bo = ctx.get("boot")
    pt = float(ctx.get("attr").loc["after", "share_pct"])
    lo, hi = bo["after"]
    ok = lo < pt < hi and 2.0 <= lo <= 7.0 and 11.0 <= hi <= 18.0 and bo["n_used"] >= 1500
    return ok, f"common-shift share {pt:.1f} %, bootstrap 95 % [{lo:.1f}, {hi:.1f}] (exp ~[4, 14]), {bo['n_used']} resamples used"


def c_cross(ctx):
    c = ctx.get("cross")
    ok = bool(c["consistent"]) and near(c["data_wait_delta_s"], 1.46, 0.15)
    return ok, f"data-wait delta {c['data_wait_delta_s']:.2f} s vs storage coef {c['storage_coef_s']:.2f} s, consistent={c['consistent']}"


def c_rank(ctx):
    ranked, rejected = ctx.get("rank")
    ids = [t["id"] for t in ranked]
    rej = {t["id"] for t in rejected}
    return ids == EXPECTED_RANK and rej == EXPECTED_REJECTED, f"order {ids}; rejected {sorted(rej)}"


def c_report(ctx):
    ranked, rejected = ctx.get("rank")
    rep = ctx.m.render_report(ctx.get("summary"), ctx.get("effects"), ctx.get("attr"), ctx.get("cross"), ranked, rejected,
                              ctx.get("boot"), "orion-n13")
    need = ["## Measured facts", "## Inferred causes", "## Remaining uncertainty", "23.2", "orion-n13", "-4.0"]
    missing = [n for n in need if n not in rep]
    order_ok = not missing and rep.index("## Measured facts") < rep.index("## Inferred causes") < rep.index("## Remaining uncertainty")
    return order_ok, "report sections present and ordered" if order_ok else f"missing or misordered: {missing}"


CHECKS = [
    ("clean_steps: dedupe + warm-up", c_clean),
    ("tp_split_jobs: TP groups spanning nodes", c_tp),
    ("job_factor_table: time-aware factor flags", c_factors),
    ("job_factor_table: failed job retained", c_failed),
    ("regression_summary: mean vs median change", c_summary),
    ("estimate_effects: per-factor OLS effects", c_effects),
    ("attribute: contributions and shares", c_attr),
    ("bootstrap_shares: job-level 95 % interval", c_boot),
    ("storage_crosscheck: direct vs inferred", c_cross),
    ("rank_tests: value/cost/risk ordering + safety", c_rank),
    ("render_report: facts / causes / uncertainty", c_report),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=sorted(IMPLS), default="starter")
    args = ap.parse_args()
    try:
        mod = load(args.impl)
    except Exception as exc:  # noqa: BLE001 - report import problems without a traceback storm
        print(f"FAIL import {IMPLS[args.impl]}: {exc!r}")
        return 2
    ctx = Ctx(mod)
    passed = 0
    for name, fn in CHECKS:
        try:
            ok, msg = fn(ctx)
            print(f"{'PASS' if ok else 'FAIL'} {name} - {msg}")
            passed += bool(ok)
        except NotImplementedError as exc:
            print(f"TODO {name} - not implemented ({exc})")
        except Exception as exc:  # noqa: BLE001
            last = traceback.extract_tb(exc.__traceback__)[-1]
            print(f"FAIL {name} - {type(exc).__name__}: {exc} (at {Path(last.filename).name}:{last.lineno})")
    print(f"\n{passed}/{len(CHECKS)} checks passed ({args.impl})")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
