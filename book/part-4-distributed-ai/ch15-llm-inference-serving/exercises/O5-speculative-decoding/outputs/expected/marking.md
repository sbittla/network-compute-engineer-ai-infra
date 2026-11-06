# Marking scheme: O5 Speculative decoding trade-off

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** two 3 × 3 tables and the recommendation with its reasoning.

| Criterion | Points |
|---|---|
| Expected tokens table E = (1 − α^(k+1)) / (1 − α) | 3 |
| Memory-bound speedup table E / (0.05k + 1) | 3 |
| Derivation of v_k at B = 128 from the roofline (1.00, 1.55, 2.67) and the resulting table | 3 |
| Recommendation: interactive k = 4 (8 only if α ≥ 0.9); throughput tier short draft k = 2 | 1 |
