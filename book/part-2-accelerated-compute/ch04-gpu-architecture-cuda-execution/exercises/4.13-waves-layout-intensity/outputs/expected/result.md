# Exercise 4.13 — waves, coalescing and intensity `[MODELED]`

| Output | Tiles | Waves (exact → launched) | Wave efficiency |
|---|---|---|---|
| 8,192 × 2,048 | (8,192 / 128) × (2,048 / 256) = 512 | 512 / 132 = 3.88 → 4 | 97 % |
| 1,024 × 2,048 | (1,024 / 128) × (2,048 / 256) = 64 | 64 / 132 = 0.48 → 1 | 48 % |

(b) Adjacent threads are 4,096 × 2 B = 8,192 B apart → 32 sectors × 32 B = 1,024 B fetched for 64 useful B = 6.25 %.

(c) Intensity of a k = n = 4,096 BF16 linear layer: m = 512: 409.6 FLOP/B, m = 256: 227.6 FLOP/B, m = 128: 120.5 FLOP/B, m = 64: 62.1 FLOP/B. Halving m from 128 to 64 scales intensity by 0.52.
