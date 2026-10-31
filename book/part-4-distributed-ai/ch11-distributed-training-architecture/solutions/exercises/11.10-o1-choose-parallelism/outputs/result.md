# 11.10 (O1) — Three workloads `[MODELED]`

| Case | Layout | States (GB) | Activations (GB) | Total (GB) | Dominant traffic per GPU per step |
|---|---|---|---|---|---|
| (a) | DP=64 (DDP or ZeRO-1), b=4 x 2 accumulation | 20.8 | 13.7 | 38.5 | DP all-reduce of 2.6 GB (5.1 GB sent, 0.028 s vs 0.26 s compute) |
| (b) | TP8 PP4 DP2 ZeRO-1 | 21.9 | 11.4 | 37.3 | TP 1.20 TB (NVLink); DP 4.38 GB, PP 2.15 GB (rail) |
| (c) | TP8 PP4 DP1 full recompute | 35.0 | 10.7 | 49.7 | TP 4.81 TB (7.2 TB with recompute, 24.1 s on NVLink); PP 8.6 GB (rail) |

(c) with selective recompute would need 183 GB of activations: impossible.
(b) alternative TP4/PP8/DP2: 48.7 GB, TP 515 GB.
