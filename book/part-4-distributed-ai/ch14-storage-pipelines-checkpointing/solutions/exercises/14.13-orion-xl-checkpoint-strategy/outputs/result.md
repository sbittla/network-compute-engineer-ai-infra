# 14.13 ORION-XL planner `[MODELED]`

| Strategy | tau (steps) | Overhead | RPO max | E[resume] | Lost GPU-h/day |
|---|---|---|---|---|---|
| async_pfs | 180 s (9) | 0.67 % | 202 s | 905 s | 662 + 9265 = 9927 |
| async_two_level | 140 s (7) | 0.49 % | 726 s | 900 s | 478 + 9964 = 10441 |
| sync_local_drain | 300 s (15) | 1.32 % | 325 s | 900 s | 1298 + 9667 = 10966 |
| sync_pfs | 700 s (35) | 3.13 % | 722 s | 905 s | 3076 + 11627 = 14702 |

Capacity: 25 TB / 5.67 TB -> 4 checkpoints (22.7 TB)
PFS burst: 5.67 TB in <t> s every 180 s (duty 12 %, average 7.9 % of write capacity)
Restart time costs 8,242 GPU-h/day; detection 300 -> 60 s saves 2,185 GPU-h/day
