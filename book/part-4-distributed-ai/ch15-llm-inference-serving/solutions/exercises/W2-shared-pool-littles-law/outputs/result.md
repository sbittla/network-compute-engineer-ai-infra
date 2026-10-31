# W2 result `[MODELED]`

t_p = 181.1 ms; demand = 4.53 replica-s/s

| Replicas | lambda_r | rho | Mean TTFT | Mean TPOT | B |
|---|---|---|---|---|---|
| 6 | 4.167 | 0.755 | 0.460 s | unstable | - |
| 8 | 3.125 | 0.566 | 0.299 s | 54.8 ms | 87.7 |
| 10 | 2.5 | 0.453 | 0.256 s | 29.7 ms | 38.0 |
| 12 | 2.083 | 0.377 | 0.236 s | 22.7 ms | 24.2 |

Choice 10 (+2 spares); worst unchunked ITL 197 ms; KV: 288 blocks/seq -> 139 sequences per replica
