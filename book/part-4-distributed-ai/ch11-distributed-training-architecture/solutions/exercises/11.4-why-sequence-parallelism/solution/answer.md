# 11.4 — Why sequence parallelism?

**Two-sentence answer.** Sequence parallelism reduces **activation memory**: the activations outside
the tensor-parallel matmuls (LayerNorm and dropout inputs/outputs, ≈ 10·s·b·h bytes per layer) are
replicated on every TP rank without it, and SP splits them along the sequence dimension across the TP
group. For TP = 8 the per-layer activation memory falls from s·b·h·(10 + 24/8) = 13·s·b·h to
s·b·h·34/8 = 4.25·s·b·h, **≈ 3.1× less**.

**Working** (Section 11.6; Korthikanti et al., 2022, with selective recompute removing the
attention-score term) `[MODELED]`:

```text
without SP: s·b·h·(10 + 24/t)    t = 8 → 10 + 3    = 13.0  ·s·b·h
with SP:    s·b·h·34/t           t = 8 → 34/8      = 4.25  ·s·b·h
ratio = 13.0 / 4.25 = 3.06
W-TRAIN, s = 4,096, b = 1, h = 8,192: 436 MB → 143 MB per layer per micro-batch
```

**Why the wire bytes do not change.** Each Megatron all-reduce becomes a reduce-scatter (leaving each
rank its sequence slice) followed later by an all-gather. An all-reduce *is* a reduce-scatter plus an
all-gather, so the total bytes on NVLink are the same; SP only changes where the work in between runs
and what each rank keeps.

**Common wrong answers.** "SP reduces TP communication" (it does not); quoting 8× (only the
replicated part shrinks by t; the matmul activations were already split); confusing SP with context
parallelism, which splits attention itself across GPUs and adds KV exchange traffic.
