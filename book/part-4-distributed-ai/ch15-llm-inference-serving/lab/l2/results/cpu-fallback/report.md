# Lab 15 L2: prefill vs decode, TTFT/ITL and KV cache memory vs the capacity model

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:59:25Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

Model: 4 layers, h=512, 8 query / 2 KV heads x 64, SwiGLU 1408, vocab 8000: **19 M params, 0.08 GB float32**. Lab model: solutions/lab/serving_lab.py.

## KV cache

Measured **4096 B/token** vs `kv_bytes_per_token` = 2 x 4 x 2 x 64 x 4 = **4096 B/token** `[MODELED]`. Full multi-head KV would be 4 x larger.

## Prefill (batch 1): compute-bound

| Prompt tokens | Median (ms) | p95 (ms) | IQR (ms) | TFLOP/s | Implied MFU |
|---|---|---|---|---|---|
| 64 | 9.50 | 11.45 | 1.13 | 0.26 | n/a |
| 256 | 28.26 | 35.75 | 7.05 | 0.36 | n/a |
| 512 | 68.69 | 69.31 | 3.79 | 0.31 | n/a |

## Decode: memory-bound (batch sweep at fixed context, then context sweep at fixed batch)

| Batch | Context | Step median (ms) | p95 (ms) | tokens/s | Effective GB/s | Lab lower bound (ms) | Implied hbm_efficiency |
|---|---|---|---|---|---|---|---|
| 1 | 256 | 1.99 | 3.72 | 503 | 39.7 | 1.32 | 0.66 |
| 4 | 256 | 2.74 | 3.78 | 1458 | 29.9 | 1.37 | 0.50 |
| 8 | 256 | 3.40 | 4.29 | 2351 | 25.4 | 1.44 | 0.42 |
| 16 | 256 | 4.36 | 6.60 | 3666 | 21.7 | 1.58 | 0.36 |
| 4 | 1024 | 3.42 | 4.32 | 1170 | 27.7 | 1.58 | 0.46 |
| 4 | 2048 | 3.68 | 4.32 | 1086 | 30.3 | 1.86 | 0.50 |

Fit t = overhead + bytes / B: **not meaningful in this run** (negative or undefined intercept). Step time was not linear in bytes moved: either the device was shared (time-slicing noise) or the step is compute/launch-bound rather than bandwidth-bound (expected for this small FP32 model on a CPU).

## Generation: batch 4, prompt 128, 32 output tokens, 5 runs

| Metric | p50 (ms) | p95 (ms) | p99 (ms) | n |
|---|---|---|---|---|
| TTFT | 48.39 | 55.39 | - | 5 |
| ITL | 2.74 | 4.97 | 6.67 | 155 |
| TPOT (per run) | 3.32 | 3.37 | - | 5 |

Lab model with its default ILLUSTRATIVE parameters (`hbm_efficiency` 0.70, 3 ms overhead) and this device's nominal DRAM rate: TPOT **4.91 ms** vs measured 3.32 ms.

## What to conclude

- Prefill time scales with prompt length at high TFLOP/s; decode step time barely moves with batch while tokens/s scales almost linearly: batch is the decode throughput lever, and the KV cache is what limits it.
- The KV formula is exact; the capacity model's uncertainty is in the reserve and fragmentation, not in bytes per token. Measure the reserve, as done here.
- The measured hbm_efficiency and overhead replace the lab's ILLUSTRATIVE 0.70 / 3 ms only for this stack (eager PyTorch). Record them in the manifest; do not copy them into configs.yaml as 'validated'.
- ITL p99 above p50 is launch and scheduling jitter on an unloaded single request stream; under real load the scheduler's prefill interruptions dominate it (Section 15.4).

_CPU fallback: no GPU was used. Bandwidth/peak invariants were skipped; efficiencies are against an ILLUSTRATIVE DRAM figure._

- Model: random-weight GQA decoder (RMSNorm, SwiGLU MLP, untied embedding/LM head), no tokenizer or download; greedy argmax sampling. Latency depends only on shapes, so random weights measure the same thing a real checkpoint of these shapes would.
- Benchmark: prefill 5 reps after 2 warm-ups, decode 20 reps after 3 warm-ups (CUDA events on the GPU); generation: 1 warm-up run then 5 runs, every step synchronised (what a client sees).
- Eager PyTorch, no CUDA graphs, no paged attention, no continuous batching: the per-step overhead measured here is Python + kernel-launch cost that engines remove; do not read it as vLLM's overhead.
- Lab model: solutions/lab/serving_lab.py.
- Not runnable here: the README's L2 serving-engine benchmark (vLLM/SGLang with an open 7-8B model; needs the network to fetch the engine and weights, and > 8 GB for BF16 7B weights + KV) and the L3 disaggregated prefill/decode over RDMA (needs 2+ nodes with RDMA NICs).
- CPU fallback: FP32 on host memory; GPU bandwidth and peak invariants were skipped, and efficiencies are expressed against a nominal 60 GB/s DRAM rate [ILLUSTRATIVE].
