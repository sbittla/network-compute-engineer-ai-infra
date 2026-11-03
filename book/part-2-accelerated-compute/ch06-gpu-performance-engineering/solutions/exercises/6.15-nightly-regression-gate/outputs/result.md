# Exercise 6.15 — nightly gate budget `[MODELED]`

| Stage | Minutes | GPU-hours (16 GPUs reserved) |
|---|---|---|
| microbenchmark suite (GEMM BF16/FP8 × 3 shapes, LayerNorm, attention) | 20 | 5.33 |
| single-node all_reduce_perf, 8 GPUs | 10 | 2.67 |
| end-to-end W-TRAIN proxy, TP = 8, 12 × 2-minute runs per node (rotating node: 6 candidate + 6 baseline interleaved; reference node: 6 + 6 baseline A/A), plus 6 min setup | 30 | 8.00 |
| Total | 60 | 16.0 of 16 |
