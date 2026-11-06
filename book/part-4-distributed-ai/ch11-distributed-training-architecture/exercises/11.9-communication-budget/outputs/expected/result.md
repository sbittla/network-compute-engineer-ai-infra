# 11.9 — Communication budget `[MODELED]`

| Dim | Bytes/GPU/step | Time (s) | Exposed (s) |
|---|---|---|---|
| TP | 1.203e+12 | 4.111 | 3.083 |
| DP | 7.656e+09 | 0.170 | 0.098 |
| PP | 2.147e+09 | 0.055 | 0.028 |

TP is 96.1 % of exposed communication and 17.7 % of the 17.45 s step: attack TP first.
TP = 2: 8 x (t-1) x M x L x B / (W x b) = 171.8 GB (TP 8 / TP 2 = 7.0).
