# 4.12 — Four bottleneck classes from the Lab 4 capture (model answer)

Relies on manuscript Section 4.11 (Table 4.4, five pathologies), Section 4.7 (occupancy) and Section 4.12.
Evidence is computed by `solve.py` directly from `lab/data/` for `train_step_41`; the trace is
`[SIMULATED]`, occupancy and roof fractions are `[MODELED]`. Equivalent evidence from a real CUDA sample on
an L2 host (for example `bandwidthTest` pageable vs pinned) is accepted if quoted with values.

| Class | Quoted evidence | Why it proves the class |
|---|---|---|
| **Launch overhead** | NVTX `optimizer_step` (5.92 ms): 600 grid-4 kernels, GPU rows 222–821; median kernel **2.61 µs**, median `cudaLaunchKernel` interval **9.31 µs**, median GPU gap 6.66 µs; the kernels are busy only 1.56 ms of the range | Kernels finish faster than the CPU can issue them: the GPU waits for launches |
| **Memory-transfer cost** | GPU row 1: `[CUDA memcpy Host-to-Device]`, `src_mem=pageable`, **100,663,296 B** in **8.26 ms** = **12.19 GB/s**; its `cudaMemcpyAsync` (correlation 1) blocks the host 8.27 ms; pinned copies in the same capture run at ≈ 48 GB/s | Pageable staging: 4× slower than pinned, host-blocking, not overlapped |
| **Occupancy constraint** | `layernorm_bwd_fused_kernel` (e.g. row 98): 256 threads, **168 registers**; 168 × 32 = 5,376 registers per warp → ⌊65,536 / 5,376⌋ = 12 warps → ⌊12 / 8⌋ = 1 block → 8 / 64 = **12.5 %**, limiter registers | Resource-limited residency |
| **Memory-bandwidth bottleneck** | Same kernel, 12 instances in step 41, 201,326,592 B each: **≈ 725 GB/s = 21.6 %** of 3.35 TB/s | Memory-bound kernel far from its roof, because of the occupancy limit above (≈ 3.3 KB in flight vs 15.2 KB needed, Exercise 4.7) |

A healthy contrast for the bandwidth class: the GELU kernels run at ≈ 83–84 % of the HBM roof. The GEMMs
are *not* an occupancy finding: 18.75 % occupancy at ≈ 62 % of the BF16 roof.

**Marking.** Full marks only with quoted values (row IDs, durations, bytes, metric values) and labels.
**Common wrong answers:** computing the pageable bandwidth from the API duration; citing GEMM occupancy as
the constraint; quoting a gap count without the launch interval that explains it.
