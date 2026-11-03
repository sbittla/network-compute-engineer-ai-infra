# 6.11 — Roofline from supplied data (model answer, 10 points)

Relies on manuscript Section 6.3 ("Empirical ceilings", "Reading kernels off the roofline", "From
classification to action") and Table 6.1. Values `[MODELED]`; `solve.py` asserts the classification and fractions.

**Method.** *I* = FLOP / DRAM bytes; compare with the ridge *of the kernel's precision* (BF16 295, FP32 SIMT
20 FLOP/B). Memory-bound: fraction = achieved bytes/s / 3.35 TB/s. Compute-bound: fraction = achieved FLOP/s /
the precision's peak.

| Kernel | *I* (FLOP/B) | Ridge | Bound | Achieved | Fraction of binding roof |
|---|---|---|---|---|---|
| K1 softmax | 1.0 × 10⁹ / 1.6 × 10⁹ = 0.625 | 295 | memory | 1.6 × 10⁹ B / 0.60 ms = 2.67 TB/s | **79.6 %** of HBM |
| K2 GEMM | 4.4 × 10¹² / 0.6 × 10⁹ = 7,333 | 295 | compute | 4.4 × 10¹² / 7.4 ms = 595 TFLOP/s | **60.1 %** of BF16 |
| K3 decode attention | 8.6 × 10⁹ / 2.15 × 10⁹ = 4.0 | 295 | memory | 2.15 × 10⁹ B / 0.75 ms = 2.87 TB/s | **85.6 %** of HBM |
| K4 reduction | 2.0 × 10¹¹ / 0.4 × 10⁹ = 500 | 20 (FP32) | compute | 2.0 × 10¹¹ / 5.0 ms = 40 TFLOP/s | **59.7 %** of FP32 |

**Fractions of the measured roofs (2 points).** Measured roofs 2.95 TB/s and 700 TFLOP/s BF16
`[ILLUSTRATIVE]`; FP32 SIMT was not measured, so K4 keeps only its vendor fraction.

| Kernel | Achieved | Fraction of measured roof | Headroom at measured roof |
|---|---|---|---|
| K1 | 2.67 TB/s | 2.67 / 2.95 = **90.4 %** | 0.60 ms × (1 − 0.904) = 0.06 ms |
| K2 | 594.6 TFLOP/s | 594.6 / 700 = **84.9 %** | 7.4 ms − 4.4 × 10¹² / 700 × 10¹² = 7.4 − 6.29 = **1.11 ms** |
| K3 | 2.87 TB/s | 2.87 / 2.95 = **97.2 %** | 0.02 ms |

The ranking does not change, but the expectations do: K2's realistic tuning gain is ≈ 1.1 ms, not the
2.95 ms the vendor roof suggests, and K1 and K3 are effectively at the roof, so only fusion or fewer bytes
helps them. Report both fractions: the vendor one for cross-site comparison, the measured one for how much
tuning is left.

**Ranking by optimization opportunity (time saved × feasibility) and lever:**

1. **K4** — 59.7 % of a roof that is itself ≈ 15× below the Tensor Core peak. Lever: move the work to Tensor
   Cores (TF32 or BF16 accumulation, if numerics allow) or restructure; up to ≈ 2 ms of 5.0 ms even on FP32.
2. **K2** — 60 % of BF16 peak, largest absolute time (≈ 2.95 ms headroom). Lever: tile configuration, library
   or autotuning; FP8 if accuracy allows (doubles the roof).
3. **K1** — near the HBM roof (≈ 0.12 ms headroom). Lever: fuse with neighbouring ops to remove the pass
   altogether, not to tune it.
4. **K3** — 85.6 % of HBM, nearly at the roof. Lever: only fewer bytes help: lower KV cache precision, batching
   more queries per KV read.

Other orderings are accepted (2 points) with a defensible time-saved × feasibility argument, as long as
each lever matches the bound (no "increase occupancy" for a near-roof memory-bound kernel).

**Common wrong answers.** Judging K4 against the BF16 roof (40 / 989 = 4 % of peak, "terrible", when it runs at
59.7 % of the FP32 SIMT roof it actually uses); reporting K1 and K3 as a fraction of peak FLOP/s.
