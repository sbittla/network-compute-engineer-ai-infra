# WP2 — FP8, TP 4, two replicas per node `[MODELED]`

- weights/GPU 17.50 GB + KV/GPU 5.37 GB = 22.87 GB
- T_memory = 6.83 ms; T_compute = 0.566 ms
- step = 10.84 ms; 2953 tokens/s per replica; 5906 per node (1.75× BF16 TP 8)
- intensity 64 FLOP/B vs FP8 balance 591 FLOP/B (9.2× below)
