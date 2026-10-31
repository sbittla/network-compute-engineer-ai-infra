"""W2 — Cost of a degraded node in W-TRAIN (Chapter 16, Section 16.6).

Usage: python solve.py --out DIR
Writes result.json and result.md; asserts the answer key (solutions/exercises-key.md).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8", newline="\n")


def close(value: float, key: float, tol: float, what: str) -> None:
    assert abs(value - key) <= tol, f"{what}: computed {value} vs key {key} (tol {tol})"


# Prompt and Section 16.6 parameters
STEP_S, GPUS = 17.4, 8 * 4 * 8            # TP 8 x PP 4 x DP 8
COMPUTE_SHARE, COMM_SHARE, GPU_SPEED = 0.70, 0.30, 0.85
GT_PER_LANE, LANES_DEGRADED, ENCODING = 32.0, 8, 128 / 130
ACHIEVED = 0.85
ALLREDUCE_GB = 1.75 * (70e9 / (8 * 4)) * 2 / 1e9    # 2 (DP-1)/DP x BF16 gradient shard
HEALTHY_GBPS = 0.9 * 50.0                           # Section 16.6: ~90 % of 400 Gb/s


def main(out: Path) -> None:
    t_new = COMPUTE_SHARE * STEP_S / GPU_SPEED + COMM_SHARE * STEP_S
    loss = 1 - STEP_S / t_new
    gpu_eq = GPUS * loss
    x16 = GT_PER_LANE * 16 * ENCODING / 8
    x8 = GT_PER_LANE * LANES_DEGRADED * ENCODING / 8
    achieved = ACHIEVED * x8
    t_degraded = ALLREDUCE_GB / achieved
    t_healthy = ALLREDUCE_GB / HEALTHY_GBPS
    extra = t_degraded - t_healthy
    extra_pct = extra / STEP_S
    ratio = loss / extra_pct

    close(t_new, 19.55, 0.005, "new step time")
    close(loss, 0.110, 0.0005, "throughput loss")
    close(gpu_eq, 28.1, 0.05, "GPU-equivalents")
    close(x8, 31.5, 0.05, "x8 ceiling GB/s")
    close(achieved, 26.8, 0.05, "achieved GB/s")
    close(ALLREDUCE_GB, 7.66, 0.005, "all-reduce GB")
    close(t_degraded, 0.286, 0.0005, "degraded all-reduce s")
    close(extra, 0.116, 0.001, "extra s per step")
    close(extra_pct, 0.0067, 0.00005, "extra fraction of step")
    assert 15 < ratio < 17, ratio

    result = {
        "exercise": "W2", "evidence_label": "[MODELED]",
        "inputs": {"step_s": STEP_S, "gpus": GPUS, "compute_share": COMPUTE_SHARE, "gpu_speed": GPU_SPEED,
                   "pcie_gt_per_lane": GT_PER_LANE, "lanes": LANES_DEGRADED, "achieved_fraction": ACHIEVED,
                   "healthy_gb_per_s": HEALTHY_GBPS},
        "answer": {"a_step_s": round(t_new, 2), "a_loss": round(loss, 4), "a_gpu_equivalents": round(gpu_eq, 1),
                   "b_x16_gb_per_s": round(x16, 1), "b_x8_gb_per_s": round(x8, 1), "b_achieved_gb_per_s": round(achieved, 1),
                   "b_allreduce_gb": round(ALLREDUCE_GB, 2), "b_healthy_s": round(t_healthy, 3),
                   "b_degraded_s": round(t_degraded, 3), "b_extra_s": round(extra, 3),
                   "b_extra_pct_of_step": round(extra_pct * 100, 2), "c_gpu_vs_nic_ratio": round(ratio, 1)},
        "units": {"time": "s", "bandwidth": "GB/s per direction"},
    }
    md = f"""
# W2 result `[MODELED]`

- (a) T = 0.7 × 17.4 / 0.85 + 0.3 × 17.4 = {t_new:.2f} s; loss {loss * 100:.1f} %; {gpu_eq:.1f} GPU-equivalents of {GPUS}
- (b) Gen5 x8 = {x8:.1f} GB/s (x16 {x16:.1f}); at 85 % {achieved:.1f} GB/s; {ALLREDUCE_GB:.2f} GB takes {t_degraded:.3f} s vs {t_healthy:.3f} s
  → +{extra:.3f} s = {extra_pct * 100:.2f} % of the step
- (c) GPU defect costs {ratio:.1f}× the NIC defect for this job
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
