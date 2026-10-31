# Exercise 1.2 — lower bounds `[MODELED]`

| Workload | Compute (s) | Memory (s) | Scale-up (s) | Scale-out (s) | Dominant | Ceiling fraction |
|---|---:|---:|---:|---:|---|---:|
| A | 0.000566 | 0.006024 | 0.000327 | 0.000000 | memory | 0.63 |
| B | 0.404449 | 0.149254 | 0.088889 | 0.600000 | scale-out | 0.40 |

If B's 30 GB moved to NVLink: 30 / 450 = 0.067 s, so B becomes compute-bound at 0.404 s.
