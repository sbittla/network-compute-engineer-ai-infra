# Lab 11 L2: scaled-down training step - measured memory and step time vs the L1 model

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:43:41Z.

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

## Cases (median of timed steps)

| Layers | Recompute | Attention | Params (M) | Step p50 (ms) | p95 (ms) | IQR (ms) | Saved act c | Peak alloc (MiB) | Achieved TFLOP/s | Kernel eff. |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | none | flash | 25.2 | 22.55 | 23.03 | 0.37 | 40.1 | 549 | 16.0 | 0.42 |
| 4 | none | flash | 50.4 | 45.15 | 46.01 | 0.57 | 38.0 | 1029 | 16.0 | 0.42 |
| 6 | none | flash | 75.6 | 67.82 | 68.76 | 0.34 | 37.4 | 1510 | 16.0 | 0.42 |
| 6 | full | flash | 75.6 | 82.80 | 83.19 | 0.41 | 5.3 | 1254 | 17.4 | 0.46 |
| 6 | none | math | 75.6 | 163.23 | 169.21 | 2.99 | 107.4 | 2659 | 6.6 | 0.17 |

## Measured vs the L1 model (Section 11.2, `stepmodel.memory_per_gpu` / `step_time`)

| Quantity | Measured | L1 model | Note |
|---|---|---|---|
| Activation coefficient c (fused attention) | 37.4 | 34 | s*b*h*c bytes per layer |
| c from allocator peak slope | 48.0 | 49.4 | saved activations + autocast BF16 weight copies (12.0), which the L1 model does not count |
| c, full recompute | 5.3 | 2 | layer input only (FP32 residual under AMP) |
| c, attention scores materialized | 107.4 | 114 | 34 + 5as/h |
| Recompute step-time ratio | 1.22 | 1.333 | 8ND vs 6ND |
| Model state | 16.23 B/param | 16 B/param | FP32 w + g + Adam m, v |
| Step time per layer | 11.32 ms | 8.11 ms | compute_s at kernel_efficiency 0.5; measured implies 0.42 |

Device peak used for efficiency: **38.2 TFLOP/s** dense BF16 `[VENDOR-SPEC]` (Ada whitepaper rate 512 BF16 FLOP/clk/SM x 24 SMs x 3105 MHz max SM clock (NVIDIA GeForce RTX 4060 Laptop GPU)).

## What to conclude

- The s*b*h*34 activation estimate holds to within the AMP dtype difference once attention is fused; materializing the scores adds the 5as/h term, which at long s dominates (Section 11.2).
- Full recomputation trades about a third more step time for an order of magnitude less activation memory: the measured ratio is the real price on this stack, not the model's 1.333.
- The kernel efficiency backed out here replaces the ILLUSTRATIVE 0.5 only for this GPU and model size; small h runs at lower efficiency than a 70B layer would.

_This is a laptop Ada GPU (RTX 4060 class, 8 GB GDDR6), not an H100 (989 dense BF16 TFLOP/s, 80 GB HBM3). The peak above uses the maximum SM clock nvidia-smi reports; the sustained laptop boost clock is lower, so the efficiencies are conservative. Compare coefficients and ratios with the L1 model, not absolute times._

- Model: pre-LN GPT block (fused QKV, causal SDPA, 4h GELU MLP), no embedding/vocab head; input is a random (s, b, h) tensor and the loss is mean(LN(x)^2). Parameters counted exactly from the module.
- Benchmark: 20 warm-up steps then 20 timed steps per case (CUDA events on the GPU, perf_counter on the CPU); median, p95, IQR reported.
- GPU numeric precision: BF16 autocast with FP32 master weights and FP32 Adam (4+4+4+4 = 16 B/param, the Section 11.2 convention). PyTorch AMP keeps the residual stream and LayerNorm inputs in FP32, which Megatron's 34 coefficient (all-BF16 activations) does not; expect c a few units above 34.
- Activation coefficient c = saved bytes / (layers x s x b x h); saved bytes are unique storages handed to autograd's pack hook, excluding parameters and autocast's BF16 weight copies (counted separately: they live until backward and show up in the allocator peak).
- Not runnable here: TP=8 with sequence parallelism and the 1F1B pipeline (needs an 8-GPU node with NVLink, README Section 8); the s*b*h*34/t division by t therefore is not measured, only the t=1 coefficient.
