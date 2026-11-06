# Marking scheme: 6.2 GB/s for elementwise, TFLOP/s for GEMM

Type knowledge-check · kind written · tier L1 · 2 points

**Evidence required:** intensity argument for both.

| Criterion | Points |
|---|---|
| Elementwise: intensity about 0.3-2 FLOP/B, far below the 295 FLOP/B ridge, so time is set by bytes and GB/s vs 3.35 TB/s is the figure of merit | 1 |
| Large GEMM: intensity in the thousands, far above the ridge, so time is set by FLOPs and TFLOP/s vs 989 TFLOP/s is the figure of merit | 1 |
