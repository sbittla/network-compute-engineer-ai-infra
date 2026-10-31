# O1 memory demand, T-tp4-fp8 `[MODELED]`

| Seq | B=16 | B=64 | B=128 | Max seqs |
|---|---|---|---|---|
| 1,024 | 75.4 GB | 91.5 GB | 112.9 GB | 625 |
| 4,096 | 91.5 GB | 155.9 GB | 241.8 GB | 156 |
| 16,384 | 155.9 GB | 413.6 GB (exceeds) | 757.2 GB (exceeds) | 39 |

KV grows as B × context and dominates the 70 GB of weights at long context.
