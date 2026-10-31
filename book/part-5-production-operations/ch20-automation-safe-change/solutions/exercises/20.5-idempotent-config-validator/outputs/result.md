# Exercise 20.5 — validator runs on the L1 fixture `[SIMULATED]`

| Run | Exit | Drift lines | Dry-run actions | Changed actions | Audit lines |
|---|---|---|---|---|---|
| run1_validate | 1 | 2 | 0 | 0 | 32 |
| run2_apply_dry_run | 1 | 2 | 1 | 0 | 33 |
| run3_apply | 0 | 2 | 0 | 1 | 33 |
| run4_apply_again | 0 | 0 | 0 | 0 | 32 |
| run5_missing_tool | 2 | 0 | 0 | 0 | 1 |

Read-back after the fix: eth3 active_mtu = 4096. Total writes: 1.
