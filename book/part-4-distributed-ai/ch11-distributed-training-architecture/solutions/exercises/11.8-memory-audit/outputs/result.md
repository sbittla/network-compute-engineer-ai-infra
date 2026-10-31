# 11.8 — Memory audit `[MODELED]`

| Item | Value |
|---|---|
| local params | 4.375e+09 |
| weights / grads / optimizer | 8.75 / 8.75 / 3.281 GB |
| model state | 20.78 GB |
| m, in flight | 32, 4 |
| activation per layer | 570.4 MB |
| activations | 45.63 GB |
| overhead | 4.0 GB |
| **total** | **70.4 GB** (fits 80 GB: True; within 68 GB: False) |

Fix b = 1: activations 22.8 GB, total 47.6 GB.
