#!/usr/bin/env python3
"""T1 — magnitude check: does the SM-clock deficit on orion-n22 GPU 5 explain the slowdown? (Section 24.12)"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Prompt values [ILLUSTRATIVE]
STEP_BEFORE_S = 17.4
STEP_AFTER_S = 19.5
SLOW_CLOCK_MHZ = 1715
PEER_CLOCK_MHZ = 1980        # peers locked at max boost, as the case states
SUSTAINED_MHZ = 1830         # ORION typical sustained clock (REFERENCE_CLUSTER), for the counterfactual
# Compute share of the step: Chapter 22 Table 22.2 budget, 13.90 s of 17.90 s [ILLUSTRATIVE]
CH22_COMPUTE_S, CH22_STEP_S = 13.90, 17.90

def write_outputs(out: Path, payload: dict, md_lines: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8", newline="\n")


def main_args() -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    return ap.parse_args().out


def main() -> None:
    out = main_args()
    share = CH22_COMPUTE_S / CH22_STEP_S
    compute = round(share * STEP_BEFORE_S, 1)                 # 13.5 s
    ratio = PEER_CLOCK_MHZ / SLOW_CLOCK_MHZ
    slowed = compute * ratio
    added = slowed - compute
    predicted = STEP_BEFORE_S + added
    pct_pred = 100 * (predicted / STEP_BEFORE_S - 1)
    pct_obs = 100 * (STEP_AFTER_S / STEP_BEFORE_S - 1)
    # counterfactual: had peers run at the 1,830 MHz sustained clock
    added_sustained = compute * (SUSTAINED_MHZ / SLOW_CLOCK_MHZ - 1)
    # inconsistent-evidence example from the key: a GPU at 58 % clock
    added_58 = compute * (1 / 0.58 - 1)

    assert abs(compute - 13.5) < 0.05
    assert abs(added - 2.1) < 0.05                             # key: +2.1 s
    assert abs(predicted - 19.5) < 0.05                        # key: 19.5 s
    assert abs(pct_pred - 12) < 0.5 and abs(pct_pred - pct_obs) < 0.5
    assert abs(100 * added_58 / STEP_BEFORE_S - 56) < 1         # key: +56 %

    payload = {"id": "T1", "evidence_label": "MODELED",
               "inputs": {"step_before_s": STEP_BEFORE_S, "step_after_s": STEP_AFTER_S,
                          "slow_clock_MHz": SLOW_CLOCK_MHZ, "peer_clock_MHz": PEER_CLOCK_MHZ,
                          "compute_share": round(share, 4)},
               "steps": {"compute_s": compute, "clock_ratio": round(ratio, 4), "slowed_compute_s": round(slowed, 2),
                         "clock_pct_of_peers": round(100 * SLOW_CLOCK_MHZ / PEER_CLOCK_MHZ, 1)},
               "answer": {"added_s_upper_bound": round(added, 2), "predicted_step_s": round(predicted, 2),
                          "predicted_pct": round(pct_pred, 1), "observed_pct": round(pct_obs, 1),
                          "explains_symptom": abs(pct_pred - pct_obs) < 0.5,
                          "added_s_if_peers_at_sustained_1830": round(added_sustained, 2),
                          "added_s_if_clock_58pct": round(added_58, 2)},
               "units": {"time": "s", "clock": "MHz"}}
    md = ["# T1 — magnitude check `[MODELED]`", "",
          f"- Compute ≈ {share:.3f} × {STEP_BEFORE_S} s = {compute} s",
          f"- Slowed compute = {compute} × {PEER_CLOCK_MHZ:,} / {SLOW_CLOCK_MHZ:,} = {slowed:.2f} s (+{added:.2f} s)",
          f"- Predicted step {predicted:.2f} s (+{pct_pred:.1f} %) vs observed {STEP_AFTER_S} s (+{pct_obs:.1f} %)",
          f"- Upper bound: memory-bound kernels scale less than the clock ratio",
          f"- Had peers run at the 1,830 MHz sustained clock, the deficit would add only {added_sustained:.2f} s"]
    write_outputs(out, payload, md)


if __name__ == "__main__":
    main()
