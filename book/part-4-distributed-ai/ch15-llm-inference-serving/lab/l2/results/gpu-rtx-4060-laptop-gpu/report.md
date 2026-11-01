# Lab 15 L2: prefill vs decode, TTFT/ITL and KV cache memory vs the capacity model

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:59:05Z.

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
| 128 | 8.47 | 8.63 | 0.16 | 20.42 | 0.53 |
| 512 | 25.01 | 25.20 | 1.35 | 28.04 | 0.72 |
| 1024 | 47.63 | 47.81 | 0.44 | 29.98 | 0.76 |
| 2048 | 98.87 | 99.96 | 2.18 | 29.93 | 0.73 |

## Decode: memory-bound (batch sweep at fixed context, then context sweep at fixed batch)

| Batch | Context | Step median (ms) | p95 (ms) | tokens/s | Effective GB/s | Lab lower bound (ms) | Implied hbm_efficiency |
|---|---|---|---|---|---|---|---|
| 1 | 512 | 7.15 | 9.12 | 140 | 189.8 | 5.30 | 0.74 |
| 2 | 512 | 7.69 | 14.05 | 260 | 178.0 | 5.35 | 0.70 |
| 4 | 512 | 7.24 | 10.05 | 553 | 192.8 | 5.45 | 0.75 |
| 8 | 512 | 7.38 | 8.86 | 1084 | 195.8 | 5.64 | 0.76 |
| 16 | 512 | 7.59 | 12.23 | 2107 | 203.5 | 6.04 | 0.80 |
| 32 | 512 | 9.02 | 10.46 | 3548 | 193.7 | 6.82 | 0.76 |
| 8 | 1024 | 7.84 | 11.96 | 1020 | 197.1 | 6.04 | 0.77 |
| 8 | 2048 | 8.02 | 12.92 | 997 | 217.8 | 6.82 | 0.85 |
| 8 | 4096 | 9.55 | 11.12 | 838 | 225.2 | 8.40 | 0.88 |

Fit t = overhead + bytes / B over both sweeps (best-of-n step times): overhead **1.12 ms**, B = **253 GB/s** (lab assumes `step_overhead_s` = 3 ms, `hbm_efficiency` = 0.70).

## Generation: batch 8, prompt 512, 64 output tokens, 5 runs

| Metric | p50 (ms) | p95 (ms) | p99 (ms) | n |
|---|---|---|---|---|
| TTFT | 183.25 | 185.75 | - | 5 |
| ITL | 7.71 | 11.35 | 17.25 | 315 |
| TPOT (per run) | 8.43 | 8.78 | - | 5 |

Lab model with its default ILLUSTRATIVE parameters (`hbm_efficiency` 0.70, 3 ms overhead) and this device's DRAM peak: TPOT **11.10 ms** vs measured 8.43 ms. Prefill of the batch at `prefill_mfu` 0.40: TTFT **360.8 ms** vs measured 183.2 ms.

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
