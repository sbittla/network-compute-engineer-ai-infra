# Marking scheme: K6 GQA and KV bytes per token

Type knowledge-check · kind computed · tier L1 · 3 points

**Evidence required:** both byte counts with the formula

| Criterion | Points |
|---|---|
| With GQA: 2 x 80 x 8 x 128 x 2 = 327,680 B/token | 1 |
| Without GQA (64 KV heads): 2,621,440 B/token, 8x more | 1 |
| Concurrency effect: 8x lower for a fixed budget (e.g. 156 → 19 sequences of 4k on TP = 4 FP8) | 1 |
