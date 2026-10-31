# O2 trace analysis `[SIMULATED]`

| Segment | req/s | out tokens/s | TTFT p50/p95 | ITL p50/p99 | Queue p95 | GPU busy | KV max | Waiting |
|---|---|---|---|---|---|---|---|---|
| baseline 0-230 s | 6.0 | 1,216 | 0.138 / 0.449 s | 21.8 / 215.9 ms | 0.11 s | 97.6 % | 13.5 % | 0.1 |
| burst 240-345 s | 14.76 | 2,980 | 11.803 / 28.814 s | 26.9 / 443.6 ms | 28.52 s | 100.0 % | 43.3 % | 46.1 |
| storm 465-600 s | 5.81 | 1,434 | 0.278 / 33.166 s | 37.2 / 386.3 ms | 32.63 s | 100.0 % | 100.0 % | 6.0 |

GPU busy is ≈ 98-100 % in every segment and cannot separate healthy, slot-bound and memory-bound.
