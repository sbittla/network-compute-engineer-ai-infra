# K6 — GQA and KV bytes per token: worked solution

**Formula (Section 15.3):** KV bytes/token = 2 (K and V) × layers × KV heads × head_dim × bytes/element.

```text
With GQA (8 KV heads):     2 × 80 × 8  × 128 × 2 B = 327,680 B   (320 KiB)
Without GQA (64 KV heads): 2 × 80 × 64 × 128 × 2 B = 2,621,440 B (2.5 MiB)   → 8× more
```

W-INFER: 80 layers, 64 query heads, 8 KV heads, head_dim 128, BF16 KV (2 B) `[MODELED]`.

**Effect on maximum concurrency.** For a fixed KV budget the number of tokens that fit falls 8×, so
concurrent sequences (or total context) fall 8×. Example for one T-tp4-fp8 replica (TP = 4, FP8 weights
70 GB, BF16 KV):

```text
KV budget = 4 × 80 GB × 0.90 − 70 GB − 4 × 2 GB = 210 GB
GQA:     blocks = ⌊210e9 / (16 × 327,680)⌋ = 40,054;  4,096-token seq = 256 blocks → 156 sequences
no GQA:  blocks = ⌊210e9 / (16 × 2,621,440)⌋ = 5,006;  → ⌊5,006 / 256⌋ = 19 sequences
```

Fewer concurrent sequences mean a smaller decode batch, so the weight read is amortized over fewer
tokens and tokens/s per GPU falls. Decode steps also stream 8× more KV bytes per sequence. GQA is one
of the main reasons a 70B model can serve large batches on 4 GPUs.

**Common wrong answers.** Using the 64 query heads in the "with GQA" case. Forgetting the factor 2 for K
and V.
