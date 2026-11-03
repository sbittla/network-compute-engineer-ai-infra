"""Exercise 20-W2 — wave plan for ORION-XL (512 HX8 nodes, 128 racks of 4).

    python solve.py --out DIR

Inputs are the prompt's stated parameters (exercises.md, Section 20.3). Detection probabilities use
the model of manuscript Section 20.7.2 (P = 1 - (1 - p)^k), plus the exact hypergeometric form.
Results are [MODELED]. Asserts the values in solutions/exercises-key.md (Section 20.3).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

NODES, RACKS, NODES_PER_RACK, GPUS_PER_NODE = 512, 128, 4, 8
WAVE_MIN = 75                  # apply + verify + 60 min bake, per wave
MAX_WAVES = 8
DEFECT_FRACTION = 0.02         # one board revision
AFFECTED_NODES = 10            # identified by inventory (≈ 2 % of 512)
CANARY = 8
TARGET_P = 0.90
STRATIFIED_AFFECTED_IN_CANARY = 2
P_MANIFEST = 0.8
PLAN = [2, 6, 24, 96, 128, 128, 128]   # reference wave plan (key 20-W2 c)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    # (a) random canary
    p_binom = 1 - (1 - DEFECT_FRACTION) ** CANARY
    p_exact = 1 - math.comb(NODES - AFFECTED_NODES, CANARY) / math.comb(NODES, CANARY)
    k_real = math.log(1 - TARGET_P) / math.log(1 - DEFECT_FRACTION)
    k_needed = math.ceil(k_real)
    assert 1 - (1 - DEFECT_FRACTION) ** k_needed >= TARGET_P > 1 - (1 - DEFECT_FRACTION) ** (k_needed - 1)

    # (b) stratified canary with two known-affected nodes
    p_strat = 1 - (1 - P_MANIFEST) ** STRATIFIED_AFFECTED_IN_CANARY

    # (c) wave plan: one node per rack per wave => wave size <= number of racks
    max_wave = RACKS
    assert sum(PLAN) == NODES and len(PLAN) <= MAX_WAVES and max(PLAN) <= max_wave and PLAN[0] <= 4
    assert all(b >= a for a, b in zip(PLAN, PLAN[1:])), "waves grow"
    # a rack has 4 nodes, so at least 4 waves are needed to touch every node in it
    assert len(PLAN) >= NODES_PER_RACK
    duration_min = len(PLAN) * WAVE_MIN
    peak_frac = max(PLAN) / NODES
    gpu_h = NODES * GPUS_PER_NODE * WAVE_MIN / 60
    cumulative = [sum(PLAN[: i + 1]) for i in range(len(PLAN))]

    # (d) detection after the first three waves under random selection
    k3 = cumulative[2]
    p_after3 = 1 - (1 - DEFECT_FRACTION) ** k3
    p_after3_exact = 1 - math.comb(NODES - AFFECTED_NODES, k3) / math.comb(NODES, k3)

    # --- assertions against solutions/exercises-key.md (20-W2) ------------------------------------
    assert abs(p_binom - 0.149) <= 0.001
    assert abs(p_exact - 0.147) <= 0.001
    assert k_needed == 114
    assert abs(p_strat - 0.96) <= 1e-9
    assert duration_min == 525 and abs(duration_min / 60 - 8.75) < 1e-9
    assert abs(peak_frac - 0.25) < 1e-9
    assert abs(gpu_h - 5_120) < 1e-6
    assert k3 == 32 and abs(p_after3 - 0.476) <= 0.001

    result = {
        "exercise": "20-W2", "evidence_label": "[MODELED]",
        "units": "probabilities (0-1), nodes, minutes, hours, GPU-hours",
        "inputs": {"nodes": NODES, "racks": RACKS, "nodes_per_rack": NODES_PER_RACK, "gpus_per_node": GPUS_PER_NODE,
                   "wave_minutes": WAVE_MIN, "max_waves": MAX_WAVES, "defect_fraction": DEFECT_FRACTION,
                   "affected_nodes": AFFECTED_NODES, "canary_nodes": CANARY, "target_probability": TARGET_P,
                   "stratified_affected_in_canary": STRATIFIED_AFFECTED_IN_CANARY, "p_manifest": P_MANIFEST},
        "steps": {"a_k_real": round(k_real, 2), "c_max_wave_size": max_wave, "c_cumulative_nodes": cumulative,
                  "d_nodes_after_three_waves": k3, "d_p_after_three_waves_exact": round(p_after3_exact, 4)},
        "answer": {"a_p_canary_binomial": round(p_binom, 4), "a_p_canary_hypergeometric": round(p_exact, 4),
                   "a_nodes_for_90pct": k_needed, "b_p_detect_stratified": round(p_strat, 4),
                   "c_wave_plan": PLAN, "c_duration_min": duration_min, "c_duration_h": round(duration_min / 60, 2),
                   "c_peak_fraction_out": round(peak_frac, 4), "c_gpu_hours": round(gpu_h, 1),
                   "d_p_after_three_waves": round(p_after3, 4)},
        "tolerance": "probabilities +/-0.001 vs the key's 3-decimal values; counts exact",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    csv = ["wave,size,cumulative_nodes,fraction_out"] + [
        f"{i},{s},{c},{s / NODES:.4f}" for i, (s, c) in enumerate(zip(PLAN, cumulative))]
    (out / "wave_plan.csv").write_text("\n".join(csv) + "\n", encoding="utf-8")
    md = [
        "# Exercise 20-W2 — result `[MODELED]`", "",
        f"a. P = 1 − 0.98^{CANARY} = {p_binom:.3f} (binomial); exact 1 − C(502, 8)/C(512, 8) = {p_exact:.3f}. "
        f"For 90 %: k ≥ ln 0.1 / ln 0.98 = {k_real:.2f} → **{k_needed} nodes**.",
        f"b. P = 1 − (1 − {P_MANIFEST})^{STRATIFIED_AFFECTED_IN_CANARY} = **{p_strat:.2f}**.",
        f"c. Plan {PLAN} (sum {sum(PLAN)}, max {max(PLAN)} = racks). Duration {len(PLAN)} × {WAVE_MIN} = "
        f"{duration_min} min = {duration_min / 60:.2f} h; peak out {peak_frac * 100:.0f} %; "
        f"GPU-h = {NODES} × {GPUS_PER_NODE} × {WAVE_MIN / 60:.2f} h = {gpu_h:,.0f}.",
        f"d. After waves 0–2 ({k3} nodes): P = 1 − 0.98^{k3} = **{p_after3:.3f}** (exact {p_after3_exact:.3f}).", "",
    ]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
