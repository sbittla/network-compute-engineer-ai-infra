# Marking scheme: 11.5 Rail locality of DP peers

Type knowledge-check · kind computed · tier L1 · 3 points

**Evidence required:** the rank arithmetic.

| Criterion | Points |
|---|---|
| Rank decomposition r = tp + 8·dp + 64·pp and rank 19 → (tp 3, dp 2, pp 0) | 1 |
| DP group {3, 11, …, 59} all have local rank 3 → GPU 3 → NIC 3 → rail leaf 3 | 1 |
| States the two assumptions (CUDA_VISIBLE_DEVICES not reordered; GPU i uses NIC i) | 1 |
