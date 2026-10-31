# Exercise 6.14 — Amdahl estimate `[MODELED]`

- Kernel time −12 %: step change = 0.04 × 0.12 = 0.48 % (speedup 1.0048×).
- 1.12× throughput: kernel time −(1 − 1/1.12) = −10.7 %, step change = 0.04 × 0.107 = 0.43 %.
- Both are below the ≈ 1 % noise floor, so "unchanged within noise" is the expected result.
- Microbenchmark input = 1 × 4,096 × 2 B = 8,192 B, which fits in the 50 MB L2: it does not exercise HBM.
