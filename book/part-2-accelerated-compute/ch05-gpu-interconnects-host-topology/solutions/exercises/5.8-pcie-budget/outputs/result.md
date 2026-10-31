# Exercise 5.8 — PCIe budget `[MODELED]`

| Link | GT/s × 128/130 × lanes / 8 | Theoretical | Achievable (≈ 80 %) | Carries 50 GB/s? |
|---|---|---|---|---|
| gen4_x16 | 16 × 128/130 × 16 / 8 | 31.5 GB/s | 25.2 GB/s | no |
| gen5_x8 | 32 × 128/130 × 8 / 8 | 31.5 GB/s | 25.2 GB/s | no |
| gen5_x16 | 32 × 128/130 × 16 / 8 | 63.0 GB/s | 50.4 GB/s | yes (tight) |

(c) With GDR the uplink carries ≈ 0 GB/s of payload. Host-staged: upstream demand = 2 × 50 (D2H for sends) + 2 × 50 (NIC writes of receives) = 200 GB/s against 63 GB/s, so each NIC gets ≈ 63 / 4 = 15.8 GB/s per direction.
