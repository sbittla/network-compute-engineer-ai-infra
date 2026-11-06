# 14.10 planner at M = 198 h `[MODELED]`

| Strategy | tau (steps) | Overhead | RPO max | Lost GPU-h/day (ckpt + fail) |
|---|---|---|---|---|
| async_pfs | 1305.0 s (75) | 0.09 % | 1323 s | 5.59 + 13.58 = 19.2 |
| async_two_level | 1061.4 s (61) | 0.07 % | 5328 s | 4.54 + 19.74 = 24.3 |
| sync_local_drain | 2105.4 s (121) | 0.15 % | 2126 s | 9.00 + 16.91 = 25.9 |
| sync_pfs | 5046.0 s (290) | 0.35 % | 5064 s | 21.71 + 29.69 = 51.4 |

Hand check (async PFS): Young = sqrt(2 × 1.188 × 712,800) = 1301.5 s -> 75 steps = 1305.0 s
Ranking unchanged; async losses fall 2.9× vs M = 48 h.
