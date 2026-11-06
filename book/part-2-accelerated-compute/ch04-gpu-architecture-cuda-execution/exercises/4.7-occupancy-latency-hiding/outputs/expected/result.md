# Exercise 4.7 — Little's law for the layernorm backward `[MODELED]`

- Needed in flight (GPU) = 3.35 × 10¹² B/s × 600 × 10⁻⁹ s = 2,010,000 B
- Needed per SM = 2,010,000 / 132 = 15,227.3 B
- Layernorm in flight per SM = 8 warps × 3.25 × 128 B = 3,328 B
- Fraction of HBM bandwidth = 3,328 / 15,227.3 = 21.9 % (≈ 0.73 TB/s)
- With one 128-B request per warp: 6.7 %
