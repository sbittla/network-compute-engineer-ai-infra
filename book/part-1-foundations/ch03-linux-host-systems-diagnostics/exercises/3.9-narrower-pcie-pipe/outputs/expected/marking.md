# Marking scheme: 3.9 The price of a narrower pipe

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** Formulas, substituted values and results with units, each labelled [MODELED].

| Criterion | Points |
|---|---|
| (a) Gen5 x16 63.0, Gen4 x16 31.5, Gen4 x2 3.94 and Gen1 x16 4.0 GB/s, with 8b/10b for Gen1 | 3 |
| (b) formulas, DP all-reduce 7.656 GB, healthy 0.170 s against degraded 0.296 s at 25.8 GB/s achievable | 2 |
| (b) numbers, at most 0.126 s extra per step and about 44 GPU-hours per day | 2 |
| (b) every result labelled [MODELED] | 1 |
| (c) keep running and repair at the next restart (1.8 GPU-h/h against 32 for DP = 7; waiting about 88 GPU-h), compared with the Gen3 x8 case (339 GPU-h/day, planned stop if repair under about 2.4 h) | 2 |
