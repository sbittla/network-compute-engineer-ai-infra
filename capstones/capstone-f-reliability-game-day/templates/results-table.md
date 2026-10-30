# Results Table

> Every row states its evidence class: `SIMULATED` (simulator output), `MODELED` (formula; show it),
> `MEASURED` (lab run with a filled manifest) or `ILLUSTRATIVE`.

| # | Result | Value | Evidence class | Source (command / file / formula) | Tier | Notes |
|---|---|---|---|---|---|---|
| 1 | Checker | `<fill: 11/11 PASS>` | SIMULATED | `python starter-kit/check.py` | L1 | |
| 2 | False alerts, fault-free 6 h (default → yours) | `<fill>` | SIMULATED | `cluster_sim.run([], rules)` | L1 | |
| 3 | Detection times (canonical) | `<fill>` | SIMULATED | | L1 | |
| 4 | Lost GPU-h, recorded game day (by fault) | `<fill>` | SIMULATED | `recovery_metrics()` | L1 | unrecovered faults are lower bounds |
| 5 | Expected lost GPU-h per node loss | `<fill>` | MODELED | `<fill: formula>` | L1 | |
| 6 | Effect of fast-fail | `<fill>` | SIMULATED | `run(..., {"fast_fail": True})` | L1 | |
| 7 | `<fill: L3 measurement>` | `<fill>` | MEASURED | `<fill>` | L3 | manifest `<fill>` |
