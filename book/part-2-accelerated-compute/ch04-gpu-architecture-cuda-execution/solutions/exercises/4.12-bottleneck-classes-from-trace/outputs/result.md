# Exercise 4.12 — four bottleneck classes in `train_step_41`

| Class | Evidence (quoted from the capture) | Label |
|---|---|---|
| Launch overhead | `optimizer_step` range (5.92 ms): 600 grid-4 kernels, rows 222–821; median kernel 2.61 µs, median `cudaLaunchKernel` interval 9.31 µs, median GPU gap 6.66 µs; kernels busy 1.56 ms of the range | `[SIMULATED]` |
| Memory-transfer cost | row 1: 100,663,296 B HtoD from pageable memory in 8.26 ms = 12.19 GB/s; its `cudaMemcpyAsync` blocks the host for 8.27 ms; pinned copies run at 48.2 GB/s | `[SIMULATED]` |
| Occupancy constraint | `layernorm_bwd_fused_kernel` (row 98): 256 threads, 168 registers → 12 warps by registers → 1 block of 8 warps → 12.5 % (registers) | `[MODELED]` |
| Memory-bandwidth bottleneck | `layernorm_bwd_fused_kernel`: 12 instances × 201,326,592 B; 725 GB/s = 21.6 % of 3.35 TB/s | `[SIMULATED]` / `[MODELED]` |
