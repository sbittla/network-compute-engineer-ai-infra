# W1 — Capacity of an alternative layout: worked solution

Constants `[VENDOR-SPEC, 2026-10]` (H100-class): HBM 3.35 TB/s and 80 GB per GPU, 989 TFLOP/s dense BF16, 1,979 TFLOP/s dense FP8. Planning factors `[ILLUSTRATIVE]` (`lab/data/configs.yaml`): HBM efficiency 0.70, 3 ms step overhead, prefill MFU 0.40, memory fraction 0.90, 2 GB reserve per GPU, 16-token blocks.
Layout: TP = 8 on one HX8, FP8 weights 70 GB, FP8 KV = 163,840 B/token (BF16: 327,680). Formulas from
Sections 15.3 and 15.2 and lab Part A. All results are `[MODELED]`.

**(a) FP8 KV.**

```text
budget  = n × HBM × mem_fraction − W − n × reserve
        = 8 × 80e9 × 0.90 − 70e9 − 8 × 2e9 = 576e9 − 70e9 − 16e9 = 490 GB
block   = 16 tokens × 163,840 B = 2,621,440 B
blocks  = ⌊490e9 / 2,621,440⌋ = 186,920
per seq = 8,192 / 16 = 512 blocks  → max = ⌊186,920 / 512⌋ = 365 sequences
```

**(b) BF16 KV.** Block = 5,242,880 B → ⌊490e9 / 5,242,880⌋ = 93,460 blocks → ⌊93,460 / 512⌋ =
**182 sequences**. FP8 KV doubles concurrency.

**(c) Decode step at B = 64, average context 6,000 tokens, FP8 KV.**

```text
bytes/step   = W + B × ctx × kv = 70e9 + 64 × 6,000 × 163,840 = 70e9 + 62.915e9 = 132.915e9 B
lower bound  = 132.915e9 / (8 × 3.35e12) = 132.915e9 / 26.8e12 = 4.96 ms → 64 / 4.96 ms = 12,905 tokens/s
planning     = 3 ms + 132.915e9 / (26.8e12 × 0.70 = 18.76e12) = 3 + 7.085 = 10.08 ms → 6,346 tokens/s
```

At this context the KV read (62.9 GB) is almost as large as the weights (70 GB). Longer contexts push
the step toward KV-dominated, which is why FP8 KV matters for a long-context tier. The planning TPOT of
10.1 ms is well inside a 50 ms SLO, so this tier could run a larger batch if KV allows (365 sequences of
8k).

**Common wrong answers.** Forgetting the 16 GB reserve (budget 506 GB). Using BF16 KV bytes in (c). Using
GiB for capacity without saying so.
