# Marking scheme: 14.3 What is in a checkpoint

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** the byte breakdown and three item → consequence pairs

| Criterion | Points |
|---|---|
| Byte breakdown 2 + 2 + 12 = 16 B training state; gradients not saved gives 14 B/param | 2 |
| First non-tensor item with its consequence (e.g. step/LR scheduler: warm-up repeats, loss jumps) | 1 |
| Second item with consequence (e.g. data-loader position and seed: replay/skip, bias) | 1 |
| Third item with consequence (e.g. RNG states or loss-scaler state) | 1 |
