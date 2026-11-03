# TS — orion-n29 arithmetic `[MODELED]`

- gap 7.0 ms / 160 all-reduces = 43.8 µs each
- all-reduces per second at 12 ms/step: 13333
- replay cost per step: 0.095 µs (negligible)
- partial NVLink loss (1/3): +1.02 µs per all-reduce, +0.163 ms per step
- DRAM active expected if the GPUs are only waiting: 0.40 (observed 0.41)
- load on the 7 remaining replicas: +14.3 %
- worst-case TPOT p95 if linear in load: 13.7 ms (SLO 50 ms)
