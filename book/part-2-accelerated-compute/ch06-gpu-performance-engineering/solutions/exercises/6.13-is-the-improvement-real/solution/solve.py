"""Exercise 6.13: run-median comparison with and without the candidate's power-capped fifth run.

Usage: python solve.py --out DIR
Uses the lab's reference permutation_test and bootstrap_ratio_ci (solutions/lab/analysis.py of this
package; seed 11, 4,000 replicates). Run medians, A/A floor (0.9 %) and threshold (2 %) from the prompt.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PKG = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PKG / "solutions" / "lab"))
import analysis  # noqa: E402  (reference implementation)

BASE = np.array([12.41, 12.37, 12.52, 12.44, 12.39, 12.47])
CAND = np.array([12.10, 12.22, 12.05, 12.31, 12.95, 12.12])
FLOOR, THRESHOLD, ALPHA = 0.009, 0.02, 0.05
# exercises-key.md 6.13: (median cand, change, ci lo, ci hi, p, decision)
KEY = {"all_runs": (12.17, -0.0205, -0.0297, 0.0165, 0.36, "not_significant"),
       "without_run5": (12.12, -0.0245, -0.0316, -0.0085, 0.002, "improvement")}


def decide(p: float, change: float) -> str:
    if p >= ALPHA:
        return "not_significant"
    if abs(change) < max(FLOOR, THRESHOLD):
        return "below_threshold"
    return "improvement" if change < 0 else "regression"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    arms = {"all_runs": CAND, "without_run5": np.delete(CAND, 4)}
    ans = {}
    for name, cand in arms.items():
        point, lo, hi = analysis.bootstrap_ratio_ci(BASE, cand, n_boot=4000, seed=11)
        p = float(analysis.permutation_test(BASE, cand))
        dec = decide(p, point)
        k = KEY[name]
        assert abs(float(np.median(cand)) - k[0]) < 1e-9
        assert abs(point - k[1]) < 0.0005 and abs(lo - k[2]) < 0.0005 and abs(hi - k[3]) < 0.0005, (name, point, lo, hi)
        assert abs(p - k[4]) < 0.005 and dec == k[5], (name, p, dec)
        ans[name] = {"n_candidate_runs": int(len(cand)), "median_candidate_ms": round(float(np.median(cand)), 3),
                     "change": round(point, 6), "ci95": [round(lo, 6), round(hi, 6)], "p_perm": round(p, 5),
                     "decision": dec}
    res = {"exercise": "6.13", "evidence_label": "MODELED (statistics on supplied run medians)",
           "inputs": {"baseline_ms": BASE.tolist(), "candidate_ms": CAND.tolist(), "floor": FLOOR,
                      "threshold": THRESHOLD, "alpha": ALPHA, "bootstrap": {"seed": 11, "replicates": 4000}},
           "steps": {"median_baseline_ms": round(float(np.median(BASE)), 3)},
           "answer": ans, "units": {"change": "fraction", "time": "ms"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Exercise 6.13 — is the improvement real?", "",
          f"Baseline median = {np.median(BASE):.3f} ms. Decision bar = max(0.9 %, 2 %) = 2 %; α = 0.05.", "",
          "| Candidate runs | Median | Change | 95 % bootstrap band | Exact permutation p | Decision |", "|---|---|---|---|---|---|"]
    for name, a in ans.items():
        md.append(f"| {name} ({a['n_candidate_runs']}) | {a['median_candidate_ms']:.3f} ms | {a['change'] * 100:+.2f} % | "
                  f"[{a['ci95'][0] * 100:+.2f} %, {a['ci95'][1] * 100:+.2f} %] | {a['p_perm']:.3f} | {a['decision']} |")
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
