# 8.16 — result `[MODELED]`

- BDP = 49,000 B/µs × 10.0 µs = **490,000 B** ≈ **120 packets** of 4,096 B
- A 4 MiB message takes 85.6 µs at 392 Gb/s

| timeout | T_ack (s) | Time to failure, retry_cnt 7 (s) | Tail cost at p = 10⁻⁷ (µs/msg) | % of a 4 MiB message |
|---|---|---|---|---|
| 14 | 0.0671 | 0.54 | 0.0067 | 0.0078 % |
| 18 | 1.0737 | 8.59 | 0.1074 | 0.1254 % |
| 20 | 4.2950 | 34.36 | 0.4295 | 0.5018 % |
