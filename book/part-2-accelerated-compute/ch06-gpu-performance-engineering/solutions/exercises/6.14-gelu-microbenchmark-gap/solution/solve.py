"""Exercise 6.14: Amdahl estimate of the end-to-end gain from a "12 % faster" GELU kernel.

Usage: python solve.py --out DIR
Inputs (prompt): GELU = 4 % of step time; "12 % faster" read two ways (time -12 %, or 1.12x throughput);
noise floor ~ 1 % (Section 6.7 / lab A/A floor order of magnitude). Microbenchmark input at batch 1,
hidden 4,096 in BF16 vs the 50 MB L2 (Table 6.1).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SHARE = 0.04
SPEEDUP_TIME = 0.12
SPEEDUP_THROUGHPUT = 1.12
NOISE_FLOOR = 0.01
MICRO_BYTES = 1 * 4_096 * 2
L2_BYTES = 50e6
KEY = {"time_reading": 0.0048, "throughput_reading": 0.0043}   # exercises-key.md 6.14
TOL = 0.0001


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    gain_time = SHARE * SPEEDUP_TIME
    kernel_cut = 1 - 1 / SPEEDUP_THROUGHPUT
    gain_tp = SHARE * kernel_cut
    overall_speedup = 1 / (1 - gain_time)
    assert abs(gain_time - KEY["time_reading"]) < TOL and abs(gain_tp - KEY["throughput_reading"]) < TOL
    assert gain_time < NOISE_FLOOR and MICRO_BYTES < L2_BYTES
    res = {"exercise": "6.14", "evidence_label": "MODELED",
           "inputs": {"gelu_share": SHARE, "kernel_time_reduction": SPEEDUP_TIME, "throughput_factor": SPEEDUP_THROUGHPUT,
                      "noise_floor": NOISE_FLOOR, "micro_input_bytes": MICRO_BYTES, "l2_bytes": L2_BYTES},
           "answer": {"step_reduction_time_reading": round(gain_time, 5),
                      "kernel_time_reduction_throughput_reading": round(kernel_cut, 4),
                      "step_reduction_throughput_reading": round(gain_tp, 5),
                      "end_to_end_speedup": round(overall_speedup, 5),
                      "below_noise_floor": gain_time < NOISE_FLOOR, "micro_input_fits_l2": MICRO_BYTES < L2_BYTES},
           "units": {"reduction": "fraction of step time"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Exercise 6.14 — Amdahl estimate `[MODELED]`

- Kernel time −12 %: step change = 0.04 × 0.12 = {gain_time * 100:.2f} % (speedup {overall_speedup:.4f}×).
- 1.12× throughput: kernel time −(1 − 1/1.12) = −{kernel_cut * 100:.1f} %, step change = 0.04 × {kernel_cut:.3f} = {gain_tp * 100:.2f} %.
- Both are below the ≈ 1 % noise floor, so "unchanged within noise" is the expected result.
- Microbenchmark input = 1 × 4,096 × 2 B = {MICRO_BYTES:,} B, which fits in the 50 MB L2: it does not exercise HBM.
"""
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
