# 12.1 — Reduce-scatter + all-gather = all-reduce

**Contracts** (Section 12.2, Table 12.2):

- **Reduce-scatter**: every rank contributes a buffer of n equal chunks; after the operation rank r
  holds only chunk r of the element-wise reduction (sum) over all ranks. Output size S/n per rank.
- **All-gather**: every rank contributes one chunk; after the operation every rank holds all n chunks,
  concatenated in rank order. Output size n × chunk on every rank.
- **All-reduce**: every rank ends with the full element-wise reduction of all buffers.

**2-rank example** `[MODELED]`: R0 = [1, 2], R1 = [10, 20], sum.

```text
reduce-scatter:  chunk 0 = 1 + 10 = 11 → R0 [11];   chunk 1 = 2 + 20 = 22 → R1 [22]
all-gather:      R0 [11, 22], R1 [11, 22]
all-reduce:      [1 + 10, 2 + 20] = [11, 22] on both ranks  ✓ identical
```

**Why it matters.** This identity is how ring all-reduce is built (2(n − 1) steps: n − 1 of
reduce-scatter, n − 1 of all-gather), why ZeRO-1 costs the same bytes as DDP (it splits the
all-reduce and inserts the optimizer step in between), and why Megatron sequence parallelism does not
change TP wire bytes (Chapter 11). Each half moves (n − 1)/n × S per rank; together 2(n − 1)/n × S —
the all-reduce busbw factor.

**Common wrong answer.** Describing reduce-scatter as "reduce then scatter the full result" so that
every rank keeps everything — that is all-reduce.
