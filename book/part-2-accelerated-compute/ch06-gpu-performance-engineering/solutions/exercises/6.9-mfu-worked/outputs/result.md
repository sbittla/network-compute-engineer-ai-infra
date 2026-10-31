# Exercise 6.9 — MFU `[MODELED]`

- tokens/s = 512 × 4,096 / 5.2 s = 2,097,152 / 5.2 = 403,298
- (a) MFU = 6 × 13 × 10⁹ × 403,298 / (64 × 989 × 10¹²) = 3.146 × 10¹⁶ / 6.330 × 10¹⁶ = 0.497
- (b) HFU = 8/6 × 0.497 = 0.663
- (c) With the FP8 peak by mistake: 3.146 × 10¹⁶ / (64 × 1,979 × 10¹²) = 0.248
- (d) 98 % GPU-Util is a duty cycle: kernels ran 98 % of the time; it says nothing about efficiency.
