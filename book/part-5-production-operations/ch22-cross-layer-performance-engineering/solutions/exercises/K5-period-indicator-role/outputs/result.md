# K5 — refit without the period indicator `[SIMULATED]`

Common shift with `after`: +0.34 ± 0.09 s/step; R² 0.9984 (with) vs 0.9978 (without).

| Term | With `after` (s) | Without (s) |
|---|---|---|
| after | +0.337 | dropped |
| tp_split | +8.961 | +9.176 |
| driver_new | +0.902 | +1.074 |
| storage_new | +1.396 | +1.565 |
| alert_node | -0.053 | +0.157 |
| tp_x_storage | -1.307 | -1.588 |

Without the indicator the common shift is pushed onto the most-exposed factors (driver +0.17 s, storage +0.17 s, TP +0.22 s) and the ECC alert gains a spurious positive effect.
