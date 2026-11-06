# Marking scheme: 14.7 Tail at scale

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** the expression 1 − q^N, values to two significant figures

| Criterion | Points |
|---|---|
| Expression 1 - q^N with q = 0.99 and 0.999 | 1 |
| 256 ranks: 0.92 (p99) and 0.23 (p99.9) | 2 |
| 4,096 ranks: about 1.0 and 0.98 | 1 |
| Interpretation: at scale the per-read p99.9 is the typical step's experience; accept storage on p99.9 or reduce exposure | 1 |
