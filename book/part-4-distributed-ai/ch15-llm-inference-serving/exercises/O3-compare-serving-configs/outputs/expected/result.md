# O3 comparison `[MODELED]`

| Config | Max seqs | Batch | TPOT | tokens/s/node | Prefill |
|---|---|---|---|---|---|
| L-tp8-bf16 | 312 | 32 | 11.68 ms | 2,740 | 90.6 ms |
| T-tp4-fp8 | 156 | 128 | 20.19 ms | 12,678 | 90.6 ms |

Latency: L-tp8-bf16; throughput: T-tp4-fp8 (4.6×)
Flips: TPOT SLO < 20.19 ms; sequences > 4992 tokens cap T below batch 128 (39 at 16k); FP8 quality.
