# Exercise 6.11 — roofline classification `[MODELED]`

| Kernel | I (FLOP/B) | Ridge | Bound | Achieved | Fraction of vendor roof | Headroom at vendor roof | Fraction of measured roof | Headroom at measured roof |
|---|---|---|---|---|---|---|---|---|
| K1 softmax | 0.625 | 295 | memory | 2.67 TB/s | 79.6 % | 0.12 ms | 90.4 % | 0.06 ms |
| K2 GEMM | 7,333.333 | 295 | compute | 594.6 TFLOP/s | 60.1 % | 2.95 ms | 84.9 % | 1.11 ms |
| K3 decode attention | 4.000 | 295 | memory | 2.87 TB/s | 85.6 % | 0.11 ms | 97.2 % | 0.02 ms |
| K4 reduction | 500.000 | 20 | compute | 40.0 TFLOP/s | 59.7 % | 2.02 ms | not measured | — |

Ranking by opportunity: K4 reduction > K2 GEMM > K1 softmax > K3 decode attention (unchanged by the measured roofs; K2's tuning headroom shrinks from 2.95 ms to 1.11 ms, K1 and K3 are effectively at the roof).
