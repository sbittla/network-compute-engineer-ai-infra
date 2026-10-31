"""Exercise 6.9: MFU, HFU with full recomputation, and the FP8-peak mistake.

Usage: python solve.py --out DIR
Inputs (prompt): 13e9 parameters, 64 GPUs, 512 sequences x 4,096 tokens per step, 5.2 s per step.
Conventions (Section 6.4): 6N FLOP per token (MFU), 8N with full activation recomputation (HFU);
dense BF16 peak 989 TFLOP/s, FP8 1,979 TFLOP/s (Table 6.1).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

N_PARAMS = 13e9
GPUS = 64
TOKENS_PER_STEP = 512 * 4_096
STEP_S = 5.2
PEAK_BF16, PEAK_FP8 = 989e12, 1_979e12
KEY = {"mfu": 0.497, "hfu": 0.663, "mfu_fp8": 0.248}   # exercises-key.md 6.9
TOL = 0.001


def sci(x: float) -> str:
    """Format as 'm.mmm × 10^e' with superscript exponent (house style)."""
    e = int(f"{x:e}".split("e")[1])
    sup = str(e).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
    return f"{x / 10**e:.3f} × 10{sup}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    tps = TOKENS_PER_STEP / STEP_S
    model_flops = 6 * N_PARAMS * tps
    mfu = model_flops / (GPUS * PEAK_BF16)
    hfu = 8 * N_PARAMS * tps / (GPUS * PEAK_BF16)
    mfu_fp8 = model_flops / (GPUS * PEAK_FP8)
    for k, v in {"mfu": mfu, "hfu": hfu, "mfu_fp8": mfu_fp8}.items():
        assert abs(v - KEY[k]) < TOL, (k, v)
    res = {"exercise": "6.9", "evidence_label": "MODELED",
           "inputs": {"params": N_PARAMS, "gpus": GPUS, "tokens_per_step": TOKENS_PER_STEP, "step_s": STEP_S,
                      "peak_bf16": PEAK_BF16, "peak_fp8": PEAK_FP8},
           "steps": {"tokens_per_s": round(tps, 1), "model_flops_per_s": model_flops,
                     "cluster_peak_bf16": GPUS * PEAK_BF16},
           "answer": {"a_mfu": round(mfu, 4), "b_hfu": round(hfu, 4), "c_mfu_fp8_mistake": round(mfu_fp8, 4)},
           "units": {"utilization": "fraction"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Exercise 6.9 — MFU `[MODELED]`

- tokens/s = 512 × 4,096 / 5.2 s = {TOKENS_PER_STEP:,} / 5.2 = {tps:,.0f}
- (a) MFU = 6 × 13 × 10⁹ × {tps:,.0f} / (64 × 989 × 10¹²) = {sci(model_flops)} / {sci(GPUS * PEAK_BF16)} = {mfu:.3f}
- (b) HFU = 8/6 × {mfu:.3f} = {hfu:.3f}
- (c) With the FP8 peak by mistake: {sci(model_flops)} / (64 × 1,979 × 10¹²) = {mfu_fp8:.3f}
- (d) 98 % GPU-Util is a duty cycle: kernels ran 98 % of the time; it says nothing about efficiency.
"""
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
