# Marking scheme: 11.8 Memory audit

Type worked-problem · kind computed · tier L1 · 6 points

**Evidence required:** every intermediate value with units.

| Criterion | Points |
|---|---|
| Local parameters 4.375e9 and model state 20.78 GB (8.75 + 8.75 + 3.28) | 2 |
| m = 32, in-flight 4, activation per layer 570.4 MB, 20 layers/stage → 45.63 GB | 2 |
| Total 70.4 GB with the 4 GB overhead; fits 80 GB but exceeds 68 GB planning limit | 1 |
| A valid fix (b = 1, full recompute, or PP = 8) with its effect | 1 |
