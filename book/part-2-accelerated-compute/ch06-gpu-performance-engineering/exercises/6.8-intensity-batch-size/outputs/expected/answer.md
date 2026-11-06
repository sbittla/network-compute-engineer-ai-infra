# 6.8 — Intensity and batch size of a BF16 linear layer (model answer, 10 points)

Relies on manuscript Section 6.2 (intensity of a GEMM) and Section 6.3 (roofline). All values `[MODELED]`;
`solve.py` asserts them. *K* = *N* = 4,096, BF16 (2 B), *P* = 989 TFLOP/s, *B* = 3.35 TB/s, ridge 295.2 FLOP/B.

**Model.** *W* = 2*MKN* FLOP. Minimum traffic *Q* = 2(*MK* + *KN* + *MN*) B (read activations and weights once,
write the output once). *I* = *W* / *Q*. Time at roof = max(*W* / *P*, *Q* / *B*).

## (a) *M* = 4,096 (4 points)

- *W* = 2 × 4,096³ = **1.374 × 10¹¹ FLOP**
- *Q* = 3 × 4,096² × 2 B = **1.007 × 10⁸ B** (100,663,296 B)
- *I* = 1.374 × 10¹¹ / 1.007 × 10⁸ = **1,365 FLOP/B** ≫ 295 → **compute-bound**
- Time at roof = 1.374 × 10¹¹ / 989 × 10¹² = **139 µs**

## (b) *M* = 64 (3 points)

- *W* = 2 × 64 × 4,096² = **2.147 × 10⁹ FLOP**
- *Q* = 2 × (64 × 4,096 + 4,096² + 64 × 4,096) = 2 × 17,301,504 = **3.460 × 10⁷ B**
- *I* = **62.1 FLOP/B** < 295 → **memory-bound**
- Time at roof = 3.460 × 10⁷ / 3.35 × 10¹² = **10.3 µs**; attainable = 62.1 × 3.35 TB/s = **208 TFLOP/s = 21 %** of
  peak. The weight matrix (33.6 MB) dominates the traffic.

## (c) Smallest compute-bound *M* (3 points)

*I*(*M*) = 2*M* × 4,096² / [2 × 4,096 × (2*M* + 4,096)] = 4,096*M* / (2*M* + 4,096). Set *I* = 295.2:
4,096*M* = 590.4*M* + 1,209,139 → *M* = 1,209,139 / 3,505.6 = 344.9 → **345 tokens**.

This is the "*I* ≈ *M*" rule of thumb (for *M* ≪ *K*, *N*), corrected for activation traffic: the naive rule says
295 tokens. Below ≈ 345 tokens per GEMM (small-batch decode, small micro-batches) the layer is memory-bound and
only fewer bytes (weight quantization, batching) speed it up.

**Common wrong answers.** Using 4 B per element; *Q* from weights only in (b) (gives 64 FLOP/B, close but
unjustified); quoting attainable 989 TFLOP/s for (b).
