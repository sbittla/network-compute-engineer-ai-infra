# Exercise 5.17 — four-NIC variant vs HX8 `[MODELED]`

n = 32 × 8 = 256; ring factor 2 × 255 / 256 = 1.99219; S / 8 = 134,217,728 B.

| Node | Rings × rate | t | busbw |
|---|---|---|---|
| HX8 (8 NICs) | 8 × 48 GB/s | 5.771 ms | 370.7 GB/s |
| Variant, 8 rings, 2 per NIC | 8 × 24 GB/s | 11.341 ms | 188.6 GB/s |
| Variant, 4 rings of S/4 | 4 × 48 GB/s | 11.341 ms | 188.6 GB/s |

The variant reaches 51 % of HX8 busbw: per-node NIC bandwidth halves (200 vs 400 GB/s).
