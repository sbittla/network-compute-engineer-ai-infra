# Exercise 4.11 — stage times `[MODELED]`

| Stage | Formula | Time |
|---|---|---|
| H2D (A and B) | 2 × 134,217,728 B / 52 × 10⁹ B/s | 5.16 ms |
| Kernel | 2 × 8,192³ = 1.0995 × 10¹² FLOP / (0.70 × 989 × 10¹² FLOP/s) | 1.59 ms |
| D2H (C) | 134,217,728 B / 52 × 10⁹ B/s | 2.58 ms |
| Total | | 9.33 ms (kernel 17 %) |

Intensity if operands cross PCIe per use: 1.0995 × 10¹² / (3 × 134,217,728) = 2,731 FLOP/B, against a PCIe
ridge of 989 × 10¹² / 52 × 10⁹ = 19,019 FLOP/B: PCIe-bound by ≈ 7.0×.
