# 13.7 result `[MODELED]`

Message S = 67.1 MB / 8 = 8.39 MB

| Path | Host copies | PCIe transfers | PCIe bytes | Time |
|---|---|---|---|---|
| gdr | 0 | 2 | 16.77 MB | 186.4 µs |
| host_staged | 2 | 4 | 33.55 MB | 521.9 µs |

GDR: 8.388e+06 B / 4e+10 B/s = 186.4 µs (+ ≈ 10 µs fixed)
Host-staged unpipelined bound: 167.8 + 186.4 + 167.8 = 521.9 µs
