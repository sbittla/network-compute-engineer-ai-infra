# Lab 11 L2: scaled-down training step - measured memory and step time vs the L1 model

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:44:07Z.

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

## Cases (median of timed steps)

| Layers | Recompute | Attention | Params (M) | Step p50 (ms) | p95 (ms) | IQR (ms) | Saved act c | Achieved GFLOP/s |
|---|---|---|---|---|---|---|---|---|
| 2 | none | flash | 1.6 | 45.87 | 49.30 | 5.51 | 68.1 | 123.4 |
| 4 | none | flash | 3.2 | 87.50 | 100.53 | 6.86 | 66.1 | 129.3 |
| 4 | full | flash | 3.2 | 111.34 | 119.03 | 9.74 | 6.0 | 135.5 |
| 4 | none | math | 3.2 | 83.16 | 92.25 | 12.26 | 106.1 | 136.1 |

## Measured vs the L1 model (Section 11.2, `stepmodel.memory_per_gpu` / `step_time`)

| Quantity | Measured | L1 model | Note |
|---|---|---|---|
| Activation coefficient c (fused attention) | 66.1 | 68 | s*b*h*c bytes per layer; FP32 so 2 x 34 |
| c, full recompute | 6.0 | 4 | layer input only (FP32 residual under AMP) |
| c, attention scores materialized | 106.1 | 148 | 34 + 5as/h |
| Recompute step-time ratio | 1.27 | 1.333 | 8ND vs 6ND |

## What to conclude

- The s*b*h*34 activation estimate holds to within the AMP dtype difference once attention is fused; materializing the scores adds the 5as/h term, which at long s dominates (Section 11.2).
- Full recomputation trades about a third more step time for an order of magnitude less activation memory: the measured ratio is the real price on this stack, not the model's 1.333.
- The kernel efficiency backed out here replaces the ILLUSTRATIVE 0.5 only for this GPU and model size; small h runs at lower efficiency than a 70B layer would.

_CPU fallback: no GPU was used. Activation bytes are exact autograd counts; step times are CPU times and say nothing about GPU efficiency. GPU-only invariants (device peak, allocator slope, 16 B/param state) were skipped._

- Model: pre-LN GPT block (fused QKV, causal SDPA, 4h GELU MLP), no embedding/vocab head; input is a random (s, b, h) tensor and the loss is mean(LN(x)^2). Parameters counted exactly from the module.
- Benchmark: 5 warm-up steps then 10 timed steps per case (CUDA events on the GPU, perf_counter on the CPU); median, p95, IQR reported.
- GPU numeric precision: BF16 autocast with FP32 master weights and FP32 Adam (4+4+4+4 = 16 B/param, the Section 11.2 convention). PyTorch AMP keeps the residual stream and LayerNorm inputs in FP32, which Megatron's 34 coefficient (all-BF16 activations) does not; expect c a few units above 34.
- Activation coefficient c = saved bytes / (layers x s x b x h); saved bytes are unique storages handed to autograd's pack hook, excluding parameters and autocast's BF16 weight copies (counted separately: they live until backward and show up in the allocator peak).
- Not runnable here: TP=8 with sequence parallelism and the 1F1B pipeline (needs an 8-GPU node with NVLink, README Section 8); the s*b*h*34/t division by t therefore is not measured, only the t=1 coefficient.
- CPU fallback: FP32 activations (4 B), so the coefficient is expected near 2 x the BF16 value; allocator peak memory is not available on the CPU and is not reported.
