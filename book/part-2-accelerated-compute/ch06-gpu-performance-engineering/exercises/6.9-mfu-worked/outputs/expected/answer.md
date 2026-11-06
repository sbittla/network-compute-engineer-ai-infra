# 6.9 — MFU of a 13B-parameter training job (model answer, 8 points)

Relies on manuscript Section 6.4 (MFU and HFU) and Table 6.1. All values `[MODELED]`; `solve.py` asserts them.

**Throughput.** tokens/s = 512 × 4,096 / 5.2 s = 2,097,152 / 5.2 = **403,298 tokens/s**.

**(a) MFU (2 points).** MFU = 6*N* × tokens/s / (GPUs × peak)
= 6 × 13 × 10⁹ × 403,298 / (64 × 989 × 10¹²) = 3.146 × 10¹⁶ / 6.330 × 10¹⁶ = **0.497 (49.7 %)**.

**(b) HFU with full activation recomputation (2 points).** The forward pass runs twice: 8*N* per token.
HFU = 8/6 × 0.497 = **0.663 (66.3 %)**.

**(c) Using the FP8 peak by mistake (2 points).** 3.146 × 10¹⁶ / (64 × 1,979 × 10¹²) = 3.146 × 10¹⁶ / 1.267 × 10¹⁷ =
**0.248**: the same BF16 job looks half as efficient. Always use the dense peak of the precision actually
trained.

**(d) What 98 % GPU-Util says (2 points).** It says kernels were executing 98 % of the time: a duty cycle
(Chapter 4 Section 4.9). It says nothing about how much of each SM's compute those kernels used. MFU does:
here half the dense BF16 peak, which is good for a 13B model on 64 GPUs. A job at 98 % GPU-Util could just as
well be at 10 % MFU.

**Common wrong answers.** Using sequences instead of tokens; forgetting the 64 GPUs in the denominator
(an impossible MFU of ≈ 31.8); reporting HFU as the efficiency figure for cross-cluster comparison.
