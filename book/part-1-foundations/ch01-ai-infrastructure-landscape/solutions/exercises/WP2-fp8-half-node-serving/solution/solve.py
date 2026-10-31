#!/usr/bin/env python3
"""WP2: FP8 W-INFER decode at TP = 4 with two replicas per HX8.

Usage: python solve.py --out DIR
Inputs: W-INFER (docs/REFERENCE_CLUSTER.md); FP8 dense peak 1,979 TFLOP/s; ceiling fraction 0.63 from the
prompt [ILLUSTRATIVE].
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def house(line: str) -> str:
    """Apply the book's copyedit house style to generated Markdown (x -> ×, ~ -> ≈, '40 %', µs)."""
    line = re.sub(r"(\d)%", r"\1 %", line)
    line = line.replace(" x ", " × ")
    line = re.sub(r"(\d)x\b", r"\1×", line)
    line = re.sub(r"~ ?", "≈ ", line)
    line = re.sub(r"(\d) us\b", r"\1 µs", line)
    return line.replace("scaleout", "scale-out").replace("scaleup", "scale-up")

PARAMS = 70e9
FP8_WEIGHTS_B = 70e9
KV_PER_TOKEN_B = 327_680
BATCH = 32
CONTEXT = 2048
TP = 4
REPLICAS_PER_NODE = 2
HBM_BPS = 3350e9
FP8_PEAK = 1979e12
FRACTION = 0.63
BF16_NODE_TOKENS = 3370      # prompt: BF16 TP = 8 per node
KEY = {"weights_GB": 17.5, "kv_gpu_GB": 5.37, "total_GB": 22.87, "T_memory_ms": 6.83,
       "T_compute_ms": 0.566, "node_tokens_s": 5900, "intensity": 64.0, "balance": 591.0}
REL_TOL = 0.01


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    weights = FP8_WEIGHTS_B / TP
    kv_rep = BATCH * CONTEXT * KV_PER_TOKEN_B
    kv_gpu = kv_rep / TP
    total = weights + kv_gpu
    t_mem = total / HBM_BPS
    flop = 2 * PARAMS * BATCH / TP
    t_cmp = flop / FP8_PEAK
    step = t_mem / FRACTION
    rep_tokens = BATCH / step
    node_tokens = REPLICAS_PER_NODE * rep_tokens
    intensity = 2 * BATCH / 1          # FLOP per byte of FP8 weight
    balance = FP8_PEAK / HBM_BPS
    ans = {"weights_GB": weights / 1e9, "kv_replica_GB": kv_rep / 1e9, "kv_gpu_GB": kv_gpu / 1e9,
           "total_GB": total / 1e9, "T_memory_ms": t_mem * 1e3, "T_compute_ms": t_cmp * 1e3,
           "step_ms": step * 1e3, "replica_tokens_s": rep_tokens, "node_tokens_s": node_tokens,
           "speedup_vs_bf16_node": node_tokens / BF16_NODE_TOKENS, "intensity": intensity,
           "balance": balance, "below_balance_x": balance / intensity}
    for k, v in KEY.items():
        assert abs(ans[k] - v) <= REL_TOL * v, (k, ans[k], v)
    assert 1.70 <= ans["speedup_vs_bf16_node"] <= 1.80
    result = {"evidence": "[MODELED]; fraction 0.63 [ILLUSTRATIVE]",
              "inputs": {"batch": BATCH, "context": CONTEXT, "tp": TP, "replicas_per_node": REPLICAS_PER_NODE,
                         "fp8_peak_tflops": FP8_PEAK / 1e12, "hbm_GBps": HBM_BPS / 1e9, "fraction": FRACTION},
              "answer": {k: round(v, 3) for k, v in ans.items()},
              "units": {"bytes": "GB (1e9)", "time": "ms", "throughput": "output tokens/s",
                        "intensity": "FLOP/B"}}
    md = ["# WP2 — FP8, TP 4, two replicas per node `[MODELED]`", "",
          f"- weights/GPU {ans['weights_GB']:.2f} GB + KV/GPU {ans['kv_gpu_GB']:.2f} GB = {ans['total_GB']:.2f} GB",
          f"- T_memory = {ans['T_memory_ms']:.2f} ms; T_compute = {ans['T_compute_ms']:.3f} ms",
          f"- step = {ans['step_ms']:.2f} ms; {ans['replica_tokens_s']:.0f} tokens/s per replica; "
          f"{ans['node_tokens_s']:.0f} per node ({ans['speedup_vs_bf16_node']:.2f}x BF16 TP 8)",
          f"- intensity {ans['intensity']:.0f} FLOP/B vs FP8 balance {ans['balance']:.0f} FLOP/B "
          f"({ans['below_balance_x']:.1f}x below)"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
