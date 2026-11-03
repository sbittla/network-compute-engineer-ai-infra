"""W1 — checkpoint interval and restart overhead with Young's first-order model (Section 19.1).

    python solve.py --out DIR

overhead ≈ δ/τ + (τ/2 + R)/M ; τ_opt ≈ sqrt(2·δ·M) ; goodput = 1 − overhead.
Inputs: prompt values plus the Reference Cluster canon (node MTBF 1,536 node-h, R = 15 min,
$3.00/GPU-h, [MODELED] from the Chapter 21 TCO). Young's model is valid only while τ ≪ M; both cases satisfy that.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

NODE_MTBF_H = 1536.0     # REFERENCE_CLUSTER.md
DELTA_MIN = 1.0          # prompt: blocking checkpoint cost
R_CANON_MIN = 15.0       # REFERENCE_CLUSTER.md restart overhead
R_FAST_MIN = 5.0         # prompt (b)
TAU_XL_MIN = 19.0        # prompt (b)
GPUS_PER_NODE = 8
PRICE_PER_GPU_H = 3.00   # prompt (c), [MODELED] (Ch 21 TCO per nominal GPU-hour, rounded)

# solutions/exercises-key.md, W1
KEY = {"a_tau_opt_min": 75.9, "a_goodput": 0.968, "b_goodput_r15": 0.811, "b_goodput_r5": 0.867,
       "c_gpu_h_per_day": 5461.0, "c_usd_per_day": 16380.0}
REL_TOL = 0.005          # 3 significant figures


def overhead(tau: float, delta: float, r: float, m: float) -> float:
    return delta / tau + (tau / 2 + r) / m


def close(a: float, b: float) -> bool:
    return abs(a - b) <= REL_TOL * abs(b)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    # (a) 32-node ORION job
    m_a = NODE_MTBF_H / 32 * 60.0
    tau_opt = math.sqrt(2 * DELTA_MIN * m_a)
    ov_a = overhead(tau_opt, DELTA_MIN, R_CANON_MIN, m_a)
    # (b) 512-node ORION-XL job
    m_b = NODE_MTBF_H / 512 * 60.0
    ov_15 = overhead(TAU_XL_MIN, DELTA_MIN, R_CANON_MIN, m_b)
    ov_5 = overhead(TAU_XL_MIN, DELTA_MIN, R_FAST_MIN, m_b)
    tau_opt_b = math.sqrt(2 * DELTA_MIN * m_b)
    # (c) value of the goodput difference
    gpus = 512 * GPUS_PER_NODE
    diff = ov_15 - ov_5                       # = (15 − 5) / 180
    gpu_h_day = diff * gpus * 24.0
    usd_day = gpu_h_day * PRICE_PER_GPU_H

    assert close(tau_opt, KEY["a_tau_opt_min"]), tau_opt
    assert close(1 - ov_a, KEY["a_goodput"]), ov_a
    assert close(1 - ov_15, KEY["b_goodput_r15"]), ov_15
    assert close(1 - ov_5, KEY["b_goodput_r5"]), ov_5
    assert close(gpu_h_day, KEY["c_gpu_h_per_day"]), gpu_h_day
    assert close(usd_day, KEY["c_usd_per_day"]), usd_day
    assert tau_opt < 0.1 * m_a and TAU_XL_MIN < 0.2 * m_b, "Young's model would be invalid"

    r4 = lambda v: round(v, 4)
    result = {
        "exercise": "W1",
        "inputs": {"node_mtbf_h": NODE_MTBF_H, "delta_min": DELTA_MIN, "r_min": [R_CANON_MIN, R_FAST_MIN],
                   "tau_xl_min": TAU_XL_MIN, "gpus_xl": gpus, "usd_per_gpu_h": PRICE_PER_GPU_H},
        "steps": {
            "a_M_min": r4(m_a), "a_tau_opt_min": r4(tau_opt), "a_checkpoint_term": r4(DELTA_MIN / tau_opt),
            "a_failure_term": r4((tau_opt / 2 + R_CANON_MIN) / m_a), "a_overhead": r4(ov_a),
            "b_M_min": r4(m_b), "b_checkpoint_term": r4(DELTA_MIN / TAU_XL_MIN),
            "b_failure_term_r15": r4((TAU_XL_MIN / 2 + R_CANON_MIN) / m_b),
            "b_failure_term_r5": r4((TAU_XL_MIN / 2 + R_FAST_MIN) / m_b),
            "b_tau_opt_min_for_reference": r4(tau_opt_b), "c_overhead_difference": r4(diff),
        },
        "answer": {"a_tau_opt_min": round(tau_opt, 1), "a_goodput": round(1 - ov_a, 3),
                   "b_goodput_r15": round(1 - ov_15, 3), "b_goodput_r5": round(1 - ov_5, 3),
                   "c_gpu_h_per_day": round(gpu_h_day, 0), "c_usd_per_day": round(usd_day, 0)},
        "units": {"tau": "min", "goodput": "fraction of wall time", "c": "GPU-h/day and USD/day"},
        "evidence_label": "[MODELED] from [ILLUSTRATIVE] inputs",
        "tolerance": f"relative {REL_TOL}",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    md = ["# W1 — Checkpoint interval and restart overhead `[MODELED]`", "",
          "overhead ≈ δ/τ + (τ/2 + R)/M; τ_opt ≈ √(2δM)", "",
          f"(a) M = 1,536/32 h = {m_a:,.0f} min; τ_opt = √(2 × 1 × {m_a:,.0f}) = {tau_opt:.1f} min; "
          f"overhead = {DELTA_MIN / tau_opt:.4f} + {(tau_opt / 2 + R_CANON_MIN) / m_a:.4f} = {ov_a:.4f} "
          f"→ goodput {(1 - ov_a) * 100:.1f} %",
          f"(b) M = {m_b:.0f} min, τ = 19: R = 15 → {ov_15:.4f} → {(1 - ov_15) * 100:.1f} %; R = 5 → {ov_5:.4f} → "
          f"{(1 - ov_5) * 100:.1f} % (τ_opt = {tau_opt_b:.1f} min either way)",
          f"(c) {diff:.4f} × {gpus:,} GPUs × 24 h = {gpu_h_day:,.0f} GPU-h/day × $3.00 = ${usd_day:,.0f}/day"]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
