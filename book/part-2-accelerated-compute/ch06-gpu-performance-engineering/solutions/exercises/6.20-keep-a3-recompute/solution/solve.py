"""Exercise 6.20: C vs A when the version-mismatch rule is dropped, so run A3 (PyTorch 2.3.1) stays in.

Usage: python solve.py --out DIR
Uses this package's lab/data and the reference compare() in solutions/lab/analysis.py. "No version rule"
is implemented by overwriting every run's driver/cuda/torch fields with the reference values in both arms,
so rule (a) never fires; the clock rule and everything else are unchanged and applied to both arms.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PKG = Path(__file__).resolve().parents[4]
DATA = PKG / "lab" / "data"
sys.path.insert(0, str(PKG / "solutions" / "lab"))
import analysis  # noqa: E402

REF = {"driver": "570.124.06", "cuda": "12.8", "torch": "2.4.0"}
KEY_WITH_RULE = {"point": -0.0050, "p": 0.026, "decision": "below_threshold"}           # Lab 6 reference
KEY_NO_RULE = {"point": -0.0044, "lo": -0.0077, "hi": 0.0119, "p": 0.99, "decision": "not_significant"}  # key 6.20


def no_version_rule(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with every run's software fields set to the reference, which disables only rule (a)."""
    d = df.copy()
    for k, v in REF.items():
        d[k] = v
    return d


def summary(r: dict) -> dict:
    return {"change": round(r["point"], 5), "ci95": [round(r["ci_lo"], 5), round(r["ci_hi"], 5)],
            "p_perm": round(float(r["p_perm"]), 4), "decision": r["decision"],
            "runs": [r["n_runs_base"], r["n_runs_cand"]], "excluded": sorted(e["run_id"] for e in r["excluded"])}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(DATA / "bench_baseline.csv", dtype={"cuda": str})
    cand = pd.read_csv(DATA / "bench_candidate_c.csv", dtype={"cuda": str})
    floor = analysis.noise_floor(pd.read_csv(DATA / "bench_aa.csv", dtype={"cuda": str}), REF)
    a3 = base[base["run_id"] == "A3"].iloc[0]
    with_rule = analysis.compare(base, cand, REF, floor)
    without = analysis.compare(no_version_rule(base), no_version_rule(cand), REF, floor)
    assert [e["run_id"] for e in with_rule["excluded"]] == ["A3"]
    assert abs(with_rule["point"] - KEY_WITH_RULE["point"]) < 0.0005 and with_rule["decision"] == KEY_WITH_RULE["decision"]
    assert abs(with_rule["p_perm"] - KEY_WITH_RULE["p"]) < 0.001
    assert not without["excluded"] and without["n_runs_base"] == 6
    assert abs(without["point"] - KEY_NO_RULE["point"]) < 0.0005, without["point"]
    assert abs(without["ci_lo"] - KEY_NO_RULE["lo"]) < 0.0005 and abs(without["ci_hi"] - KEY_NO_RULE["hi"]) < 0.0005
    assert abs(without["p_perm"] - KEY_NO_RULE["p"]) < 0.01 and without["decision"] == KEY_NO_RULE["decision"]
    a3_med = float(base[(base["run_id"] == "A3") & (base["iter"] >= analysis.WARMUP_ITERS)]["latency_ms"].median())
    others = base[(base["run_id"] != "A3") & (base["iter"] >= analysis.WARMUP_ITERS)].groupby("run_id")["latency_ms"].median()
    a3_rel = a3_med / float(others.median()) - 1
    res = {"exercise": "6.20", "evidence_label": "SIMULATED data; MODELED statistics",
           "inputs": {"reference_sw": REF, "a3_torch": str(a3["torch"]), "noise_floor": round(floor, 5)},
           "steps": {"a3_median_ms": round(a3_med, 4), "a3_vs_other_baseline_runs": round(a3_rel, 4)},
           "answer": {"with_version_rule": summary(with_rule), "without_version_rule": summary(without)},
           "units": {"change": "fraction"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 6.20 — C vs A with and without the version rule", "",
          f"Run A3 (PyTorch {a3['torch']}) median is {a3_rel * 100:+.1f} % vs the other baseline runs.", "",
          "| Protocol | Baseline runs | Change | 95 % band | Permutation p | Decision |", "|---|---|---|---|---|---|"]
    for name, r in (("version rule (A3 excluded)", with_rule), ("no version rule (A3 kept)", without)):
        md.append(f"| {name} | {r['n_runs_base']} | {r['point'] * 100:+.2f} % | [{r['ci_lo'] * 100:+.2f} %, "
                  f"{r['ci_hi'] * 100:+.2f} %] | {float(r['p_perm']):.3f} | {r['decision']} |")
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
