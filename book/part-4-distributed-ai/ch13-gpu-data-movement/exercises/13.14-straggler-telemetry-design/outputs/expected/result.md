# 13.14 volume estimate `[MODELED]`

- steps/day = 86,400 / 2 = 43,200; sampled every 10 -> 4,320
- bytes/sample = 4,096 × 20 × 8 B = 655,360 B
- per-rank stream = 2.83 GB/day (every step: 28.3 GB/day)
- DCGM 1 Hz, 10 fields/GPU = 28.3 GB/day (node agent, already collected)
