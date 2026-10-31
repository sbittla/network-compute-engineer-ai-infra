# 11.12 (O3) — Checkpoint plan `[MODELED]`

| Scenario | tau_opt (min) | Waste opt | Waste 4 h | Failures/day | Lost s/failure | GPU-h/failure | GPU-h/day |
|---|---|---|---|---|---|---|---|
| orion256_sync_pfs | 65.7 | 2.80 % | 5.0 % | 0.5 | 2872 | 204 | 102 |
| orion256_async_staged | 21.9 | 1.28 % | 4.7 % | 0.5 | 1557 | 111 | 55 |
| orionxl4096_sync_pfs | 16.4 | 17.46 % | invalid | 8.0 | 1393 | 1585 | 12679 |
| orionxl4096_async_staged | 5.5 | 11.38 % | invalid | 8.0 | 1064 | 1211 | 9688 |

XL async decomposition: C/tau 1.52 %, tau/2MTBF 1.52 %, R/MTBF 8.33 %
