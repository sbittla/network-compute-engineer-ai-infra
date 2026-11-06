# Exercise 6.8 — intensity and batch size `[MODELED]`

Ridge = 989 / 3.35 = 295.2 FLOP/B.

| M | W (FLOP) | Q (B) | I (FLOP/B) | Bound | Time at roof | Attainable |
|---|---|---|---|---|---|---|
| 4,096 | 1.374 × 10¹¹ | 100,663,296 | 1,365.3 | compute | 139.0 µs | 989 TFLOP/s (100 %) |
| 64 | 2.147 × 10⁹ | 34,603,008 | 62.1 | memory | 10.3 µs | 208 TFLOP/s (21 %) |

(c) I(M) = 4,096 M / (2M + 4,096) = 295.2 → M = 295.2 × 4,096 / (4,096 − 2 × 295.2) = 344.9 → smallest compute-bound M = 345 tokens.
