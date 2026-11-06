# Marking scheme: 13.5 Overlap window for the DP reduction

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** the window and its W-TRAIN value with arithmetic

| Criterion | Points |
|---|---|
| Identifies the window: only compute that does not depend on the reduced gradients, the last micro-batch's backward on the stage | 2 |
| Arithmetic 13.9 s / 128 x 2/3 = 72 ms | 2 |
| Compares with about 170 ms DP time: about 98 ms exposed, labelled [MODELED] | 1 |
