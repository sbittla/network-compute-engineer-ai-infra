# Marking scheme: 6.8 Intensity and batch size

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** all arithmetic; label `[MODELED]`.

| Criterion | Points |
|---|---|
| (a) M = 4,096: W = 1.374e11 FLOP, Q = 1.007e8 B, I = 1,365 FLOP/B, compute-bound, 139 µs at roof | 4 |
| (b) M = 64: W = 2.147e9 FLOP, Q = 3.460e7 B, I = 62.1 FLOP/B, memory-bound, 10.3 µs at roof, 208 TFLOP/s = 21 % of peak | 3 |
| (c) I(M) = 4,096M / (2M + 4,096) = 295.2 gives M = 345 tokens; labelled [MODELED] | 3 |
