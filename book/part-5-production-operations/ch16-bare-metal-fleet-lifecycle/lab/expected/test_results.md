# Test results: ch16

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.197 |
| `test_lab_starter_fails_gracefully` | PASS | 0.182 |
| `test_lab_runs_without_generator` | PASS | 0.722 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 0.253 |
| `test_exercise_index` | PASS | 0.030 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| D1-acceptance-spec-runbook | 4 | PASS | [test_results.md](../../exercises/D1-acceptance-spec-runbook/outputs/expected/test_results.md) |
| DC1-tiered-return-to-service | 4 | PASS | [test_results.md](../../exercises/DC1-tiered-return-to-service/outputs/expected/test_results.md) |
| K1-lifecycle-states | 4 | PASS | [test_results.md](../../exercises/K1-lifecycle-states/outputs/expected/test_results.md) |
| K2-pcie-idle-downtraining | 4 | PASS | [test_results.md](../../exercises/K2-pcie-idle-downtraining/outputs/expected/test_results.md) |
| K3-row-remap-pending-failure | 4 | PASS | [test_results.md](../../exercises/K3-row-remap-pending-failure/outputs/expected/test_results.md) |
| K4-throttle-reasons | 4 | PASS | [test_results.md](../../exercises/K4-throttle-reasons/outputs/expected/test_results.md) |
| K5-validated-bundles | 4 | PASS | [test_results.md](../../exercises/K5-validated-bundles/outputs/expected/test_results.md) |
| K6-redfish-resources | 4 | PASS | [test_results.md](../../exercises/K6-redfish-resources/outputs/expected/test_results.md) |
| K7-nvme-sanitize-purge | 4 | PASS | [test_results.md](../../exercises/K7-nvme-sanitize-purge/outputs/expected/test_results.md) |
| L1-fleet-lifecycle-lab | 4 | PASS | [test_results.md](../../exercises/L1-fleet-lifecycle-lab/outputs/expected/test_results.md) |
| M1-node-acceptance-design | 4 | PASS | [test_results.md](../../exercises/M1-node-acceptance-design/outputs/expected/test_results.md) |
| M2-compat-matrix-upgrade-plan | 4 | PASS | [test_results.md](../../exercises/M2-compat-matrix-upgrade-plan/outputs/expected/test_results.md) |
| M3-lifecycle-state-machine | 4 | PASS | [test_results.md](../../exercises/M3-lifecycle-state-machine/outputs/expected/test_results.md) |
| R1-deriving-thresholds | 4 | PASS | [test_results.md](../../exercises/R1-deriving-thresholds/outputs/expected/test_results.md) |
| R2-correlated-failures | 4 | PASS | [test_results.md](../../exercises/R2-correlated-failures/outputs/expected/test_results.md) |
| R3-missing-evidence-nccl-hang | 4 | PASS | [test_results.md](../../exercises/R3-missing-evidence-nccl-hang/outputs/expected/test_results.md) |
| R4-fw-off-matrix-decision | 4 | PASS | [test_results.md](../../exercises/R4-fw-off-matrix-decision/outputs/expected/test_results.md) |
| T1-afternoon-slowdown | 4 | PASS | [test_results.md](../../exercises/T1-afternoon-slowdown/outputs/expected/test_results.md) |
| W1-staged-upgrade-orion-xl | 4 | PASS | [test_results.md](../../exercises/W1-staged-upgrade-orion-xl/outputs/expected/test_results.md) |
| W2-degraded-node-cost | 4 | PASS | [test_results.md](../../exercises/W2-degraded-node-cost/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
