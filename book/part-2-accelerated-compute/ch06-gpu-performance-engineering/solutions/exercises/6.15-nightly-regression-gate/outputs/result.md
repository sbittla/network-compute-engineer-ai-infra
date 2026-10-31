# Exercise 6.15 — nightly gate budget `[MODELED]`

| Stage | Minutes | GPU-hours (16 GPUs reserved) |
|---|---|---|
| microbenchmark suite (GEMM BF16/FP8 × 3 shapes, LayerNorm, attention) | 20 | 5.33 |
| single-node all_reduce_perf, 8 GPUs | 10 | 2.67 |
| end-to-end W-TRAIN proxy, TP = 8, 6 × 3-minute runs incl. A/A pair, plus setup | 30 | 8.00 |
| Total | 60 | 16.0 of 16 |
