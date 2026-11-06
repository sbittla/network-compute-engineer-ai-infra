# 14.20 result `[MODELED]`

| Layout | Formula | Create time (s) |
|---|---|---|
| (a) one directory, 1,025 files/rank | 262,400 / 2,700 | 97.2 |
| (b) one subdirectory per rank | max(262,400 / 30,000, 1,025 / 2,700) | 8.75 |
| (c) one directory, 2 files/rank | 512 / 2,700 | 0.190 |

(d) budget 5% x 18.49 s = 0.9245 s -> 2,496 creates -> 9.75 per rank -> **9 files per rank**.
