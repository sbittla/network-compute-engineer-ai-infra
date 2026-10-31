# 6.2 — Why GB/s for elementwise kernels and TFLOP/s for large GEMMs (model answer, 2 points)

Relies on manuscript Sections 6.2–6.3 (roofline) and Exercise 6.1's ridge (295 FLOP/B, dense BF16).

**Elementwise kernel (1 point).** An elementwise op such as a BF16 add or GELU reads one or two inputs and
writes one output: a few FLOPs per 4–6 bytes, so *I* ≈ 0.3–2 FLOP/B, two orders of magnitude below the
295 FLOP/B ridge. Its time is set entirely by bytes moved: *t* ≈ bytes / bandwidth. Even at the roof it uses
< 1 % of the compute peak, so TFLOP/s is a meaningless figure for it. The meaningful figure is achieved
bandwidth against 3.35 TB/s (e.g. GELU at ≈ 83–84 % of the HBM roof is healthy).

**Large GEMM (1 point).** An *M* = *N* = *K* = 8,192 BF16 GEMM does 2*N*³ ≈ 1.1 × 10¹² FLOP on ≈ 4 × 10⁸ B
of operands: *I* in the thousands (≈ 2,730 FLOP/B), far above the ridge. Its time is set by FLOPs, so the
figure of merit is achieved TFLOP/s against 989 TFLOP/s (Lab 6: 70 % of peak). Quoting its GB/s would look
"poor" while it is in fact excellent.

**Rule.** Report each kernel against its *binding* roof: the one the roofline says limits it.

**Common wrong answer.** "GEMMs are compute-heavy and elementwise kernels are light" without the intensity
argument; or judging every kernel by % of peak FLOP/s.
