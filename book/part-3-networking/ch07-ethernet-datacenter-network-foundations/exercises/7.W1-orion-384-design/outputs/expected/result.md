# 7.W1 — result `[MODELED]`

| Quantity | (a) rail-optimized 1:1 | (b) `size_two_tier(384, 64, 64, 1.0)` | (c) rail-optimized 3:1 |
|---|---|---|---|
| Down / up per leaf | 32 / 32 | 32 / 32 | 48 / 16 |
| Leaves (per rail) | 16 (2) | 12 (not rail-aware) | 8 (1) |
| Spines | 8 | 8 | 2 |
| Links per leaf-spine pair | 4 | 4 | 8 |
| Downlinks used / total | 384 / 512 (75.0 %) | — | 384 / 384 |
| Host + fabric cables | 384 + 512 = 896 | 384 + 384 = 768 | 384 + 128 = 512 |
| Transceivers (before spares) | 1,792 | 1,536 | 1,024 |

(a) ratio 1:1 as configured, 0.75:1 as used. (c) cross-leaf 6.4 Tb/s vs downlink 19.2 Tb/s per leaf.
