# WP1 — Re-partitioning W-TRAIN as TP 4 × PP 8 × DP 8

Method: manuscript Section 1.5 ("How much traffic, and where?", Table 1.6), with the ceiling model of
Section 1.6. W-TRAIN parameters from `docs/REFERENCE_CLUSTER.md`: 70 × 10⁹ parameters, 80 layers, hidden
8,192, 4,194,304 tokens per step, BF16 (2 B). All results `[MODELED]`; peak rates, perfect efficiency, no
overlap. `solve.py` reproduces every line.

**Shared quantities.** Tokens per DP replica = 4,194,304 / 8 = 524,288. Layers per stage = 80 / 8 = 10.
Per-all-reduce activation payload = 524,288 × 8,192 × 2 B = **8.59 GB**. It does *not* shrink when the
TP degree changes, because every TP rank holds the full activation tensor before the reduction.

**(a) Tensor parallel (p = 4).**

```text
S_TP      = 4 all-reduces/layer × 10 layers × 8.59 GB   = 343.6 GB
sent/GPU  = 2(p − 1)/p × S_TP = 2 × 3/4 × 343.6 GB      = 1.5 × 343.6 = 515.4 GB
T_scaleup = 515.4 GB / 450 GB/s                         = 1.145 s
```

**(b) Data parallel (p = 8).** Parameters per GPU = 70 × 10⁹ / (TP 4 × PP 8) = 2.1875 × 10⁹, the same as
the baseline because TP × PP = 32 either way.

```text
gradient shard = 2.1875e9 × 2 B          = 4.375 GB
sent/GPU       = 1.75 × 4.375 GB         = 7.66 GB
T_scaleout     = 7.66 GB / 50 GB/s       = 0.153 s
```

**(c) Pipeline.** A stage boundary carries 8.59 GB forward (activations) and 8.59 GB backward (gradients),
split over the 4 TP ranks with sequence parallelism: 8.59 / 4 = 2.15 GB per GPU per direction. A
middle-stage GPU sends forward to the next stage and backward to the previous one: 2 × 2.15 = **4.30 GB**,
4.30 / 50 = **0.086 s** if both boundaries cross nodes. With PP 8 on 4-GPU TP groups, two stages share a
node, so every other boundary is intra-node and can ride NVLink. Most GPUs then put only ≈ 2.15 GB
(0.043 s) on the NIC. Worst case on the NIC: 7.66 + 4.30 = **11.95 GB → 0.239 s**.

**(d) Comparison.**

| Per GPU per step | TP 8 / PP 4 (Table 1.6) | TP 4 / PP 8 |
|---|---|---|
| TP bytes sent, NVLink bound | 1,202.6 GB, 2.67 s | 515.4 GB, 1.145 s |
| NIC bytes (worst case), bound | 9.8 GB, 0.196 s | 11.95 GB, 0.239 s |
| Compute bound | 6.96 s | 6.96 s |

The new layout cuts the NVLink lower bound by 57 % and raises the worst-case NIC bound by 22 %. Both stay
well below the 6.96 s compute bound, so on the ceiling model alone the change looks attractive.

**Unmodeled cost: the pipeline bubble.** In a 1F1B schedule the first and last stages idle while the
pipeline fills and drains. The idle fraction ≈ (p − 1)/(m + p − 1). With m = 64 micro-batches
`[ILLUSTRATIVE]`: PP 4 → 3/67 = **4.5 %**; PP 8 → 7/71 = **9.9 %**. The extra ≈ 5.4 % of a 17.4 s step
(≈ 0.94 s) eats most of the 1.5 s NVLink saving, which in any case partly overlaps with compute. Also
acceptable: more activation memory in flight for deeper pipelines, and more point-to-point latency per
micro-batch.

**Common wrong answers:** using 1.75 for p = 4 (gives 601 GB and 1.34 s); dividing parameters by TP only
(gives 17.5 × 10⁹ per GPU); shrinking the per-all-reduce payload with the TP degree; ignoring that half
the pipeline boundaries are intra-node.
