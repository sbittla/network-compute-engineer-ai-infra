# D1 sizing `[MODELED]`

t_p = 362.2 + 27.8 = 390.0 ms

| P | rho | mean TTFT | p95 TTFT (exact M/D/1) |
|---|---|---|---|
| 12 | 0.65 | 0.752 s | 1.71 s |
| 13 | 0.6 | 0.682 s | 1.49 s |
| 14 | 0.557 | 0.635 s | 1.35 s |

| D | TPOT | B |
|---|---|---|
| 3 | 25.1 ms | 50.2 |
| 4 | 18.6 ms | 27.9 |
| 5 | 16.1 ms | 19.3 |

Choice 14P + 4D -> 10 nodes incl. spare
KV 2.684 GB/req; aggregate 429.5 Gb/s; RDMA 7.9 % (15.8 ms); TCP 107.4 % (infeasible)
