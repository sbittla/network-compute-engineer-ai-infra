# D1 — Hot spares vs elastic training `[MODELED]`

M = 180 min; mean in repair = 40; p99 pool = 55; re-packed replicas = ⌊472/8⌋ = 59; expected replicas lost unpacked = 30.8

| Option | Goodput | Capacity factor | Useful per fleet node |
|---|---|---|---|
| A_hot_spares | 0.811 | 0.903 | 0.733 |
| B_repacked | 0.867 | 0.922 | 0.799 |
| B_not_repacked_expected | 0.867 | 0.519 | 0.450 |
| B_not_repacked_worst | 0.867 | 0.375 | 0.325 |
