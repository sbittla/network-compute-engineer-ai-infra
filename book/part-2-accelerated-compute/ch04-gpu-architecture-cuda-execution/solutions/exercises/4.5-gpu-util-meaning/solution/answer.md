# 4.5 — What nvidia-smi `utilization.gpu` measures (model answer)

Relies on manuscript Section 4.9 and Table 4.5.

**Definition.** `utilization.gpu` (NVML GPU utilization) is the percent of time over the past sample period
during which **one or more kernels was executing** on the GPU. It is a duty cycle: it says nothing about
how many SMs the kernel used or how efficiently.

**Example `[MODELED]`.** A loop launches 600 back-to-back kernels of 4 thread blocks each. Each block runs on
one SM, so at most 4 of 132 SMs are active: 4 / 132 = **3 %** of the SMs. Some kernel is always executing,
so GPU-Util reads **100 %**. Even if those 4 SMs ran at full rate, delivered throughput would be ≤ 3 % of
peak; in practice tiny elementwise kernels run far below per-SM peak, so delivered FLOP/s is < 1 % of
989 TFLOP/s. The Lab 4 optimizer comb (600 grid-4 kernels) is exactly this pattern.

**Two DCGM fields that reveal it** (names `[VENDOR-SPEC, 2026-10]`):

- `DCGM_FI_PROF_SM_ACTIVE` — fraction of time at least one warp is resident on an SM, averaged over all SMs;
  here ≈ 0.03.
- `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` — fraction of cycles the tensor pipe is active; ≈ 0 for elementwise work.
- Also acceptable: `DCGM_FI_PROF_SM_OCCUPANCY` (resident warps relative to the maximum) and
  `DCGM_FI_PROF_DRAM_ACTIVE` (fraction of cycles the memory interface is busy). DCGM 4.6+ renames the ratio
  fields (`..._SM_UTIL_RATIO` etc.) and keeps the old names as aliases.

**Diagnostic rule.** GPU-Util high but SM-active or tensor-active low → small kernels or low parallelism;
all high but throughput low → inefficient kernels (Chapter 6).

**Common wrong answers.** "Percent of SMs in use" or "percent of peak FLOP/s": both are what the metric
does *not* measure.
