# Results Table

> Every row states its evidence class. `SIMULATED` = computed on the synthetic dataset; `MODELED` =
> computed from a formula and stated assumptions (show it); `MEASURED` = produced on stated hardware
> with a filled manifest; `ILLUSTRATIVE` = a teaching value.

| # | Result | Value | Evidence class | Source (command / file / formula) | Tier | Notes |
|---|---|---|---|---|---|---|
| 1 | Checker | `<fill: 17/17 PASS>` | SIMULATED | `python starter-kit/check.py` | L1 | |
| 2 | Nodes tested this week (and how many passed) | `<fill>` | SIMULATED | `evaluate_acceptance()` | L1 | |
| 3 | Nodes rejected and reasons | `<fill>` | SIMULATED | | L1 | |
| 4 | Nodes on non-golden stacks | `<fill>` | SIMULATED | `check_compatibility()` | L1 | |
| 5 | Rollout waves / cap per wave | `<fill>` | MODELED | `plan_waves()` + cap formula | L1 | |
| 6 | Planned unavailability of rollout | `<fill> GPU-h` | MODELED | `<fill: formula>` | L1 | |
| 7 | Canary decisions S1–S4 | `<fill>` | SIMULATED | `canary_decision()` | L1 | |
| 8 | Audit verification | `<fill>` | SIMULATED | `audit_verify()` | L1 | |
| 9 | `<fill: e.g. measured ib_write_bw on lab node>` | `<fill>` | MEASURED | `<fill>` | L3 | manifest: `<fill>` |
