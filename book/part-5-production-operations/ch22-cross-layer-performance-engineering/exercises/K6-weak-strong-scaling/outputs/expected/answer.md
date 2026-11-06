# K6 — Weak- and strong-scaling efficiency (solution)

**Formulas (Section 22.5.1).**

```text
Strong scaling (fixed global problem):   E_strong(N) = (T(N0) × N0) / (T(N) × N)
Weak scaling   (fixed per-GPU work):     E_weak(N)   = X(N) / ((N / N0) × X(N0)),   X = tokens/s
```

With per-GPU work constant, the weak-scaling formula reduces to `E_weak = T(N0) / T(N)`, because X(N)
grows with N only through the batch.

**Which applies: weak scaling.** Going from the 64-GPU ablation (TP = 8, PP = 4, DP = 2) to the 256-GPU
run (TP = 8, PP = 4, DP = 8) keeps TP and PP fixed and grows only data parallelism. The global batch
grows with DP from 256 to 1,024 sequences of 4,096 tokens (1,048,576 → 4,194,304 tokens per step), so
each GPU processes the same micro-batches and holds the same 70e9 / 32 ≈ 2.19 × 10⁹ parameters. What
is held constant is the per-GPU work, which is the definition of weak scaling.

**Illustration with the chapter's numbers** `[ILLUSTRATIVE]`: 17.38 s (64 GPUs) and 17.90 s (256 GPUs)
give E_weak = 17.38 / 17.90 = 97.1 %. Using the strong-scaling formula on the same times would give
(17.38 × 64)/(17.90 × 256) = 24.3 %, a meaningless number because the problem was not fixed.

**Common wrong answers.** Using strong-scaling efficiency because "more GPUs were added"; computing
efficiency from step times without noting that the batch changed.
