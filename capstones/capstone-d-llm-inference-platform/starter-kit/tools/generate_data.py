#!/usr/bin/env python3
"""Generate the Capstone D inputs for W-INFER serving on ORION HX8 nodes.

Writes (byte-identical on every run with the same seed):
  trace_s1.csv .. trace_s5.csv   five independent 15-minute traces (seeds seed+1 .. seed+5) for one
                       node at node load 1.0 (~5 req/s): arrival_s, prompt_tokens, output_tokens, tenant
                       (Poisson arrivals; lognormal lengths; a 2 % long-context RAG tenant, ~32k prompts)
  model.yaml           W-INFER architecture (docs/REFERENCE_CLUSTER.md §3)
  hardware.yaml        HX8 per-GPU HBM capacity/bandwidth, peak FLOP/s, efficiency assumptions
  configs.yaml         four candidate serving configurations
  slo.yaml             SLO targets and the error-budget window
  economics.yaml       illustrative GPU-hour price and fleet utilization
  vendor_sizing_sheet.csv   a third-party sizing sheet (one figure in it uses the wrong unit)

All values are [ILLUSTRATIVE]; the trace is synthetic. Usage:
    python tools/generate_data.py [--out ../data] [--seed 77]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import yaml

DURATION_S = 900.0     # 15 minutes: >= 10 minutes of steady state after warm-up/cool-down exclusion
RATE_PER_S = 5.0
N_SEEDS = 5


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    ap.add_argument("--seed", type=int, default=77)
    args = ap.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    for k in range(1, N_SEEDS + 1):
        r = np.random.default_rng(args.seed + k)
        n_req = int(DURATION_S * RATE_PER_S * 1.2)
        arrivals = np.cumsum(r.exponential(1.0 / RATE_PER_S, n_req))
        n = int(np.searchsorted(arrivals, DURATION_S))
        arrivals = arrivals[:n]
        prompt = np.clip(r.lognormal(np.log(1400), 0.6, n), 64, 8000).astype(int)
        output = np.clip(r.lognormal(np.log(220), 0.7, n), 8, 1024).astype(int)
        tenant = np.array(["chat"] * n, dtype=object)
        rag = r.random(n) < 0.02
        prompt[rag] = r.integers(30000, 32500, rag.sum())
        output[rag] = r.integers(150, 400, rag.sum())
        tenant[rag] = "rag-long"
        lines = ["request_id,arrival_s,prompt_tokens,output_tokens,tenant"]
        for i in range(n):
            lines.append(f"s{k}q{i:05d},{arrivals[i]:.4f},{prompt[i]},{output[i]},{tenant[i]}")
        (out / f"trace_s{k}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    _ = rng

    def dump(name: str, obj: dict) -> None:
        (out / name).write_text(yaml.safe_dump(obj, sort_keys=False, width=100), encoding="utf-8", newline="\n")

    dump("model.yaml", {"name": "W-INFER 70B dense, GQA", "params": 70.0e9, "layers": 80, "hidden": 8192,
                        "q_heads": 64, "kv_heads": 8, "head_dim": 128, "kv_dtype_bytes": 2,
                        "weight_bytes_per_param": {"bf16": 2, "fp8": 1}})
    dump("hardware.yaml", {"node": "HX8", "gpus_per_node": 8,
                           "hbm_bytes_per_gpu": 80.0e9, "hbm_bw_bytes_per_s": 3.35e12,
                           "peak_flops": {"bf16": 989.0e12, "fp8": 1979.0e12},
                           "hbm_bw_efficiency": 0.70, "prefill_mfu": 0.50,
                           "runtime_reserve_bytes_per_gpu": 4.0e9,
                           "iteration_overhead_s": {"8": 0.0030, "4": 0.0022},
                           "provenance": "VENDOR-SPEC 2026-10 class values for H100-SXM; efficiencies ILLUSTRATIVE"})
    dump("configs.yaml", {"configs": {
        "c1_bf16_tp8_chunked": {"tp": 8, "dtype": "bf16", "max_num_seqs": 256, "max_num_batched_tokens": 2048,
                                "chunked_prefill": True, "max_model_len": 32768, "gpu_memory_utilization": 0.90,
                                "replicas_per_node": 1},
        "c2_bf16_tp8_bigbatch": {"tp": 8, "dtype": "bf16", "max_num_seqs": 512, "max_num_batched_tokens": 32768,
                                 "chunked_prefill": False, "max_model_len": 32768, "gpu_memory_utilization": 0.90,
                                 "replicas_per_node": 1},
        "c3_fp8_tp4_chunked": {"tp": 4, "dtype": "fp8", "max_num_seqs": 256, "max_num_batched_tokens": 2048,
                               "chunked_prefill": True, "max_model_len": 32768, "gpu_memory_utilization": 0.90,
                               "replicas_per_node": 2},
        "c4_bf16_tp8_len8k": {"tp": 8, "dtype": "bf16", "max_num_seqs": 256, "max_num_batched_tokens": 2048,
                              "chunked_prefill": True, "max_model_len": 8192, "gpu_memory_utilization": 0.90,
                              "replicas_per_node": 1},
    }})
    dump("slo.yaml", {"ttft_p95_s": 0.8, "ttft_reference_prompt_tokens": 2048, "tpot_p95_s": 0.050,
                      "itl_p99_s": 0.100, "frontend_budget_s": 0.030,
                      "warmup_exclude_s": 60, "cooldown_exclude_s": 60,
                      "availability": 0.999, "window_days": 30,
                      "note": "TTFT target applies to prompts up to 2,048 tokens; longer prompts are reported separately"})
    dump("economics.yaml", {"gpu_hour_usd": 2.20, "fleet_utilization": 0.65,
                            "provenance": "ILLUSTRATIVE fully loaded internal cost per GPU-hour for ORION"})
    (out / "vendor_sizing_sheet.csv").write_text(
        "item,value,unit,source\n"
        "weights_bf16,140,GB,sizing sheet v3\n"
        "kv_cache_per_token,320,KB,sizing sheet v3\n"
        "hbm_per_gpu,80,GB,sizing sheet v3\n", encoding="utf-8", newline="\n")
    print(f"wrote dataset to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
