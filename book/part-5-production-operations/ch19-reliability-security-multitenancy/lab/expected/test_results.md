# Test results: ch19

**PASS**: 98 passed, 0 skipped, 98 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 1.584 |
| `test_lab_starter_fails_gracefully` | PASS | 1.454 |
| `test_lab_runs_without_generator` | PASS | 2.113 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 1.458 |
| `test_exercise_index` | PASS | 0.054 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| D1-hot-spares-vs-elastic | 4 | PASS | [test_results.md](../../exercises/D1-hot-spares-vs-elastic/outputs/expected/test_results.md) |
| K1-scale-and-mtbf | 4 | PASS | [test_results.md](../../exercises/K1-scale-and-mtbf/outputs/expected/test_results.md) |
| K10-threat-model-evidence | 4 | PASS | [test_results.md](../../exercises/K10-threat-model-evidence/outputs/expected/test_results.md) |
| K2-row-remapper-states | 4 | PASS | [test_results.md](../../exercises/K2-row-remapper-states/outputs/expected/test_results.md) |
| K3-reading-xids | 4 | PASS | [test_results.md](../../exercises/K3-reading-xids/outputs/expected/test_results.md) |
| K4-pcie-evidence | 4 | PASS | [test_results.md](../../exercises/K4-pcie-evidence/outputs/expected/test_results.md) |
| K5-first-reporter | 4 | PASS | [test_results.md](../../exercises/K5-first-reporter/outputs/expected/test_results.md) |
| K6-domain-vs-unit | 4 | PASS | [test_results.md](../../exercises/K6-domain-vs-unit/outputs/expected/test_results.md) |
| K7-gpu-sharing-tenants | 4 | PASS | [test_results.md](../../exercises/K7-gpu-sharing-tenants/outputs/expected/test_results.md) |
| K8-reachability-vs-performance | 4 | PASS | [test_results.md](../../exercises/K8-reachability-vs-performance/outputs/expected/test_results.md) |
| K9-silent-data-corruption | 4 | PASS | [test_results.md](../../exercises/K9-silent-data-corruption/outputs/expected/test_results.md) |
| L1-lab19-orion-xl-incident | 4 | PASS | [test_results.md](../../exercises/L1-lab19-orion-xl-incident/outputs/expected/test_results.md) |
| M1-failure-mode-analysis | 4 | PASS | [test_results.md](../../exercises/M1-failure-mode-analysis/outputs/expected/test_results.md) |
| M2-tenant-isolation-boundaries | 4 | PASS | [test_results.md](../../exercises/M2-tenant-isolation-boundaries/outputs/expected/test_results.md) |
| M3-recovery-containment-exercise | 4 | PASS | [test_results.md](../../exercises/M3-recovery-containment-exercise/outputs/expected/test_results.md) |
| M4-512-node-incident | 4 | PASS | [test_results.md](../../exercises/M4-512-node-incident/outputs/expected/test_results.md) |
| R1-intervention-evidence | 4 | PASS | [test_results.md](../../exercises/R1-intervention-evidence/outputs/expected/test_results.md) |
| R2-clock-skew | 4 | PASS | [test_results.md](../../exercises/R2-clock-skew/outputs/expected/test_results.md) |
| R3-aggressive-auto-quarantine | 4 | PASS | [test_results.md](../../exercises/R3-aggressive-auto-quarantine/outputs/expected/test_results.md) |
| R4-most-severe-violation | 4 | PASS | [test_results.md](../../exercises/R4-most-severe-violation/outputs/expected/test_results.md) |
| T1-quiet-downtrain | 4 | PASS | [test_results.md](../../exercises/T1-quiet-downtrain/outputs/expected/test_results.md) |
| W1-checkpoint-interval-restart | 4 | PASS | [test_results.md](../../exercises/W1-checkpoint-interval-restart/outputs/expected/test_results.md) |
| W2-retry-budgets-spares | 4 | PASS | [test_results.md](../../exercises/W2-retry-budgets-spares/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
