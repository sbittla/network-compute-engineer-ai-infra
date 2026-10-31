"""13.8 -- Straggler amplification: P(at least one slow rank) and GPU time lost. [MODELED]

Usage: python solve.py --out DIR
Inputs: the prompt (p = 0.05 %; N = 256, 1,024, 4,096; 64 ranks, 774 vs 600 ms, 924 ms step).
Formulas: manuscript Section 13.7.
"""
import argparse
import json
from pathlib import Path

P_SLOW = 0.0005
NS = (256, 1024, 4096)
RANKS = 64
SLOW_MS, NORMAL_MS, STEP_MS = 774.0, 600.0, 924.0
KEY_PROB = {256: 0.120, 1024: 0.401, 4096: 0.871}   # solutions/exercises-key.md 13.8 (a)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    probs = {n: 1 - (1 - P_SLOW) ** n for n in NS}
    for n in NS:
        assert abs(probs[n] - KEY_PROB[n]) < 0.0015, (n, probs[n])   # tolerance 0.15 points
    lost_gpu_s = (RANKS - 1) * (SLOW_MS - NORMAL_MS) / 1e3
    frac = lost_gpu_s / (RANKS * STEP_MS / 1e3)
    assert abs(lost_gpu_s - 10.96) < 0.01, lost_gpu_s     # key: 10.96 GPU-s per step
    assert abs(frac - 0.185) < 0.001, frac                 # key: 18.5 %

    result = {
        "inputs": {"p": P_SLOW, "N": list(NS), "ranks": RANKS, "slow_ms": SLOW_MS,
                   "normal_ms": NORMAL_MS, "step_ms": STEP_MS},
        "steps": {"formula_a": "1 - (1 - p)^N", "formula_b": "sum_r (max a - a_r) / (N * T_step)",
                  "waiting_ranks": RANKS - 1},
        "answer": {"p_at_least_one_slow": {str(n): round(probs[n], 4) for n in NS},
                   "lost_gpu_s_per_step": round(lost_gpu_s, 2), "lost_fraction": round(frac, 4)},
        "units": {"lost_gpu_s_per_step": "GPU-seconds", "probabilities": "fraction"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# 13.8 result `[MODELED]`", "", "(a) P = 1 - (1 - 0.0005)^N", ""]
    lines += [f"- N = {n:,}: {probs[n]*100:.1f} %" for n in NS]
    lines += ["", f"(b) lost = 63 × ({SLOW_MS:.0f} - {NORMAL_MS:.0f}) ms = {lost_gpu_s:.2f} GPU-s per step; "
              f"fraction = {lost_gpu_s:.2f} / (64 × {STEP_MS/1e3:.3f} s) = {frac*100:.1f} %", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
