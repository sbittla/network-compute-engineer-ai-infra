# 4.13 — Batch size and data layout (model answer)

Relies on manuscript Section 4.8 (Tensor Cores, batch size and data layout) and Section 4.4 (coalescing).
Values `[MODELED]`; `solve.py` asserts (a) and (b) and checks the intensity scaling in (c).

## (a) Tiles, waves and wave efficiency (128 × 256 tiles, 132 SMs, one tile per SM per wave)

| Output | Tiles | Waves | Efficiency |
|---|---|---|---|
| 8,192 × 2,048 | (8,192 / 128) × (2,048 / 256) = 64 × 8 = **512** | 512 / 132 = 3.88 → **4** | 3.88 / 4 = **97 %** |
| 1,024 × 2,048 | 8 × 8 = **64** | 64 / 132 = 0.48 → **1** | only 64 of 132 SMs busy: **48 %** |

The small batch leaves more than half the GPU idle for the whole kernel, regardless of how fast each tile is.

## (b) Column access of a row-major [8,192, 4,096] BF16 tensor

In row-major layout consecutive elements of a *row* are adjacent. Walking dimension 0 with adjacent threads
means adjacent threads are one row apart: 4,096 × 2 B = **8,192 B**. Every thread lands in its own 32-B
sector for 2 useful bytes: 32 × 2 = 64 useful B per 32 × 32 = 1,024 B fetched = **6.25 %** efficiency, so a
memory-bound kernel reaches at most ≈ 6 % of the HBM roof in useful bytes.

Fixes (any two): map adjacent threads to adjacent *columns* (iterate dimension 1 across the warp);
materialize the transposed layout once (`.t().contiguous()`) if it is read many times; load coalesced tiles
into shared memory and transpose there (padding to avoid bank conflicts).

## (c) Halving the batch

For a linear layer with *m* tokens and a *k* × *n* weight: FLOPs = 2*mkn*, bytes ≈ 2(*mk* + *kn* + *mn*) in
BF16. When *m* ≪ *k*, *n* the weight term dominates and intensity ≈ 2*mkn* / 2*kn* = ***m* FLOP/B**. Halving the
batch therefore roughly halves intensity (for *k* = *n* = 4,096: 120.5 FLOP/B at *m* = 128, 62.1 at
*m* = 64) and pushes the GEMM below the 295 FLOP/B BF16 ridge toward the memory roof (Chapter 6). nvidia-smi
GPU-Util is a duty cycle: a kernel is running the whole time either way, so it stays near 100 % whether the
GEMM runs at 60 % or 15 % of peak.

**Common wrong answers.** Using fractional waves as the time (the last partial wave costs a full wave);
claiming a smaller batch "improves occupancy"; 12.5 % in (b) (that is the FP32 case of Exercise 4.2).
