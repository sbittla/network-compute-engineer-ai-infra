# Marking scheme: 6.11 Roofline from supplied data

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** table with intensity, ridge, bound, fraction of vendor roof and of measured roof; ranked list with levers.

| Criterion | Points |
|---|---|
| K1 (I = 0.625, memory, 79.6 % of HBM) and K2 (I = 7,333, compute, 60.1 % of BF16) rows correct | 3 |
| K3 (I = 4.0, memory, 85.6 % of HBM) and K4 (I = 500 vs FP32 ridge 20, compute, 59.7 % of FP32) rows correct | 3 |
| Fractions of the measured roofs: K1 90.4 %, K2 84.9 %, K3 97.2 % (K4 not measured); ranking unchanged, K2 tuning headroom 1.11 ms rather than 2.95 ms | 2 |
| Ranking by opportunity with the right lever per bound (K4 tensor cores/TF32-BF16, K2 tiles/library/FP8, K1 fusion, K3 fewer bytes) | 2 |
