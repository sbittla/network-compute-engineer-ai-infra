# Marking scheme: 11.2 Bytes per parameter

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** a breakdown and three numbers.

| Criterion | Points |
|---|---|
| Breakdown: 2 B BF16 weights, 2 B BF16 gradients, 12 B FP32 optimizer state (4 master + 4 m + 4 v) | 2 |
| ZeRO-1 with DP = 8: 5.5 B | 1 |
| ZeRO-2 with DP = 8: 3.75 B | 1 |
| ZeRO-3 with DP = 8: 2.0 B (plus transient gather buffers) | 1 |
