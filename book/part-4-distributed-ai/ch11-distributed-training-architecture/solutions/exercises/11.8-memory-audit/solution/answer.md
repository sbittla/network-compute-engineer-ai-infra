# 11.8 — Memory audit: TP 4, PP 4, DP 16, micro-batch 2, ZeRO-1, selective recompute

Method: Section 11.2 (memory accounting), Table 11.4 assumptions (80 GB HBM, 85 % headroom → 68 GB
planning limit, 4 GB fixed overhead). All values `[MODELED]`, GB = 10⁹ B.

```text
P (local params)   = 70e9 / (TP × PP) = 70e9 / 16                   = 4.375e9
weights   2P       = 8.75 GB
gradients 2P       = 8.75 GB
optimizer 12P/DP   = 12 × 4.375e9 / 16                               = 3.281 GB
model state                                                          = 20.78 GB

m (micro-batches)  = global batch / (DP × b) = 1,024 / (16 × 2)      = 32
in flight, stage 0 = min(PP, m) = min(4, 32)                         = 4
activation/layer   = s·b·h·34/TP = 4,096 × 2 × 8,192 × 34 / 4         = 570.4 MB
layers per stage   = 80 / 4                                          = 20
activations        = 570.4 MB × 20 × 4                               = 45.63 GB

total = 20.78 + 45.63 + 4.0 (overhead)                               = 70.4 GB
```

**Verdict.** 70.4 GB **fits in 80 GB but exceeds the 68 GB planning limit** (85 % headroom), so it is
not acceptable. This is planted trap J in the lab (`memory_traps`: "68..80: fits, violates headroom").

**Fixes.** Micro-batch 1: activations halve to 22.8 GB → total 47.6 GB (m doubles to 64, which also
shrinks the bubble from 3/35 to 3/67). Or full recompute (activations ≈ 2/34 of today's), or PP = 8
(10 layers per stage, but 8 micro-batches in flight on stage 0 — check the product).

**Common wrong answers.** Forgetting the in-flight factor (11.4 GB activations and a false
"comfortable"); dividing weights or gradients by DP under ZeRO-1; using 80 GB as the limit; omitting
the 4 GB overhead.
