# Marking scheme: O1 Memory demand vs batch, sequence length and concurrency

Type outline-mandated · kind computed · tier L1 · 6 points

**Evidence required:** the 3 × 3 table, the max-sequence row, and the explanation.

| Criterion | Points |
|---|---|
| 3 x 3 table of weights + KV for B = 16/64/128 and 1k/4k/16k | 3 |
| Cells above 288 GB marked (16k at B = 64 and 128) | 1 |
| Max concurrent sequences 625 / 156 / 39 | 1 |
| Two-sentence explanation: KV grows as B x context and dominates; concurrency falls inversely with length | 1 |
