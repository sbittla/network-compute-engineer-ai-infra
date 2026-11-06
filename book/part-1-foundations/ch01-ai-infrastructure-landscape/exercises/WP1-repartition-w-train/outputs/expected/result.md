# WP1 — TP 4 / PP 8 vs TP 8 / PP 4 `[MODELED]`

| Per GPU per step | TP 8 / PP 4 | TP 4 / PP 8 |
|---|---:|---:|
| TP bytes sent (GB) | 1202.6 | 515.4 |
| NVLink bound (s) | 2.672 | 1.145 |
| DP bytes sent (GB) | 7.66 | 7.66 |
| PP bytes sent, middle stage (GB) | 2.15 | 4.29 |
| NIC worst case (GB / s) | 9.80 / 0.196 | 11.95 / 0.239 |
| Compute bound (s) | 6.96 | 6.96 |
| 1F1B bubble at m = 64 | 4.5 % | 9.9 % |
