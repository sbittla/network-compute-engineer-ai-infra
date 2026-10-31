# Lab 15 L2: prefill vs decode, TTFT/ITL and KV cache memory vs the capacity model

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:51:23Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

Model: 12 layers, h=2048, 16 query / 4 KV heads x 128, SwiGLU 5632, vocab 32000: **672 M params, 1.34 GB bfloat16**. Lab model: solutions/lab/serving_lab.py.

## KV cache

Measured **24576 B/token** vs `kv_bytes_per_token` = 2 x 12 x 4 x 128 x 2 = **24576 B/token** `[MODELED]`. Full multi-head KV would be 4 x larger.

Capacity model for this GPU (`kv_budget_bytes`, `max_concurrent_sequences`): 8.0 GiB x 0.90 - weights 1.34 GB - measured activation reserve 138 MB = **6.25 GB** of KV -> 62 sequences of 4,096 tokens, 248 of 1,024 `[MODELED]`.

## Prefill (batch 1): compute-bound

| Prompt tokens | Median (ms) | p95 (ms) | IQR (ms) | TFLOP/s | Implied MFU |
|---|---|---|---|---|---|
| 128 | 21.16 | 21.79 | 0.51 | 8.17 | 0.21 |
| 512 | 62.28 | 63.25 | 1.10 | 11.26 | 0.29 |
| 1024 | 125.39 | 127.07 | 1.61 | 11.39 | 0.29 |
| 2048 | 258.49 | 260.51 | 2.11 | 11.45 | 0.28 |

## Decode: memory-bound (batch sweep at fixed context, then context sweep at fixed batch)

| Batch | Context | Step median (ms) | p95 (ms) | tokens/s | Effective GB/s | Lab lower bound (ms) | Implied hbm_efficiency |
|---|---|---|---|---|---|---|---|
| 1 | 512 | 15.85 | 16.98 | 63 | 85.6 | 5.30 | 0.33 |
| 2 | 512 | 17.62 | 19.25 | 113 | 77.7 | 5.35 | 0.30 |
| 4 | 512 | 17.72 | 18.31 | 226 | 78.7 | 5.45 | 0.31 |
| 8 | 512 | 18.15 | 19.94 | 441 | 79.6 | 5.64 | 0.31 |
| 16 | 512 | 19.92 | 20.26 | 803 | 77.6 | 6.04 | 0.30 |
| 32 | 512 | 23.92 | 25.03 | 1338 | 73.0 | 6.82 | 0.29 |
| 8 | 1024 | 19.17 | 19.75 | 417 | 80.6 | 6.04 | 0.31 |
| 8 | 2048 | 21.85 | 22.39 | 366 | 80.0 | 6.82 | 0.31 |
| 8 | 4096 | 25.70 | 26.29 | 311 | 83.7 | 8.40 | 0.33 |

Fit t = overhead + bytes / B over both sweeps (best-of-n step times): overhead **0.34 ms**, B = **84 GB/s** (lab assumes `step_overhead_s` = 3 ms, `hbm_efficiency` = 0.70).

## Generation: batch 8, prompt 512, 64 output tokens, 5 runs

| Metric | p50 (ms) | p95 (ms) | p99 (ms) | n |
|---|---|---|---|---|
| TTFT | 489.18 | 491.39 | - | 5 |
| ITL | 18.69 | 20.02 | 24.41 | 315 |
| TPOT (per run) | 18.80 | 19.22 | - | 5 |

Lab model with its default ILLUSTRATIVE parameters (`hbm_efficiency` 0.70, 3 ms overhead) and this device's DRAM peak: TPOT **11.10 ms** vs measured 18.80 ms. Prefill of the batch at `prefill_mfu` 0.40: TTFT **360.8 ms** vs measured 489.2 ms.

Device peaks `[VENDOR-SPEC]`: 38.2 TFLOP/s BF16, 256 GB/s DRAM (BF16 512 FLOP/clk/SM x 24 SMs x 3105 MHz (Ada whitepaper); DRAM 8001 MHz x 2 x bus width (NVIDIA spec)).

## What to conclude

- Prefill time scales with prompt length at high TFLOP/s; decode step time barely moves with batch while tokens/s scales almost linearly: batch is the decode throughput lever, and the KV cache is what limits it.
- The KV formula is exact; the capacity model's uncertainty is in the reserve and fragmentation, not in bytes per token. Measure the reserve, as done here.
- The measured hbm_efficiency and overhead replace the lab's ILLUSTRATIVE 0.70 / 3 ms only for this stack (eager PyTorch). Record them in the manifest; do not copy them into configs.yaml as 'validated'.
- ITL p99 above p50 is launch and scheduling jitter on an unloaded single request stream; under real load the scheduler's prefill interruptions dominate it (Section 15.6).

_Laptop RTX 4060 (8 GB GDDR6, ~256 GB/s), not an H100 (80 GB HBM3, 3.35 TB/s): ratios and shapes transfer, absolute latencies do not._

- Model: random-weight GQA decoder (RMSNorm, SwiGLU MLP, untied embedding/LM head), no tokenizer or download; greedy argmax sampling. Latency depends only on shapes, so random weights measure the same thing a real checkpoint of these shapes would.
- Benchmark: prefill 5 reps after 2 warm-ups, decode 20 reps after 3 warm-ups (CUDA events on the GPU); generation: 1 warm-up run then 5 runs, every step synchronised (what a client sees).
- Eager PyTorch, no CUDA graphs, no paged attention, no continuous batching: the per-step overhead measured here is Python + kernel-launch cost that engines remove; do not read it as vLLM's overhead.
- Lab model: solutions/lab/serving_lab.py.
- Not runnable here: the README's L2 serving-engine benchmark (vLLM/SGLang with an open 7-8B model; needs the network to fetch the engine and weights, and > 8 GB for BF16 7B weights + KV) and the L3 disaggregated prefill/decode over RDMA (needs 2+ nodes with RDMA NICs).
