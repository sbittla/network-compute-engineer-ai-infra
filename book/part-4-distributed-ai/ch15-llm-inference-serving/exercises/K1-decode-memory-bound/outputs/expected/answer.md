# K1 — Why decode is memory-bound: worked solution

**Answer (Section 15.2).** Arithmetic intensity is FLOPs per byte read from HBM. A decode step at batch
32 does about 2N FLOP per token × 32 tokens while streaming all N BF16 weights (2N bytes) once:
intensity ≈ 2N·32 / 2N = **32 FLOP/B**. Attention over the KV cache is lower still. With GQA each KV
element (2 B) serves 64/8 = 8 query heads at 2 FLOP per multiply-add, so intensity ≈ **8 FLOP/B**,
independent of batch. Both are far below the H100-class BF16 ridge of 989 × 10¹² / 3.35 × 10¹² ≈
**295 FLOP/B**, so decode is HBM-bandwidth-bound: the Tensor Cores wait on memory. A 2,048-token prefill
reuses each weight byte for 2,048 tokens: intensity ≈ 2N·2048 / 2N = **2,048 FLOP/B**, about 7× above
the ridge, so prefill is compute-bound. `[MODELED]`

| Phase | Intensity | vs ridge 295 FLOP/B | Bound |
|---|---|---|---|
| Decode, B = 32 (weights) | ≈ 32 FLOP/B | 0.11× | HBM bandwidth |
| Decode attention (GQA) | ≈ 8 FLOP/B | 0.03× | HBM bandwidth |
| Prefill, 2,048 tokens | ≈ 2,048 FLOP/B | 6.9× | Compute |

**Consequence.** Decode speed scales with bytes moved per step (weights + KV), which is why FP8 weights,
FP8 KV and batching help TPOT. Prefill scales with FLOPs, which is why TP and MFU set TTFT.

**Common wrong answer.** Computing intensity per token (2 FLOP per parameter ÷ 2 B = 1 FLOP/B) instead
of per weight byte read once for the whole batch.
