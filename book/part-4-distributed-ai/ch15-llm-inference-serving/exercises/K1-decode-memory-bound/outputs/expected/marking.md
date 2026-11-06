# Marking scheme: K1 Why decode is memory-bound

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** both intensities (approximate is fine) compared with the ridge in FLOP/B

| Criterion | Points |
|---|---|
| Decode intensity at B = 32 about 32 FLOP/B (attention about 8 FLOP/B with GQA) | 2 |
| Prefill intensity for 2,048 tokens about 2,048 FLOP/B | 2 |
| BF16 ridge 989 / 3.35 = 295 FLOP/B and the comparison | 1 |
