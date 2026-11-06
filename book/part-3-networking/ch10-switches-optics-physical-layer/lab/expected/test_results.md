# Test results: ch10

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.695 |
| `test_lab_starter_fails_gracefully` | PASS | 0.686 |
| `test_lab_runs_without_generator` | PASS | 1.118 |
| `test_lab_golden_solution_report` | PASS | 0.004 |
| `test_lab_golden_starter_report` | PASS | 0.727 |
| `test_exercise_index` | PASS | 0.056 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 10.D1-expansion-pod-media-plan | 4 | PASS | [test_results.md](../../exercises/10.D1-expansion-pod-media-plan/outputs/expected/test_results.md) |
| 10.H1-link-health-analyzer | 4 | PASS | [test_results.md](../../exercises/10.H1-link-health-analyzer/outputs/expected/test_results.md) |
| 10.K1-counter-pipeline-stages | 4 | PASS | [test_results.md](../../exercises/10.K1-counter-pipeline-stages/outputs/expected/test_results.md) |
| 10.K2-pam4-fec-corrected-counter | 4 | PASS | [test_results.md](../../exercises/10.K2-pam4-fec-corrected-counter/outputs/expected/test_results.md) |
| 10.K3-rs544-parameters | 4 | PASS | [test_results.md](../../exercises/10.K3-rs544-parameters/outputs/expected/test_results.md) |
| 10.K4-crc-stomping | 4 | PASS | [test_results.md](../../exercises/10.K4-crc-stomping/outputs/expected/test_results.md) |
| 10.K5-dr4-vs-fr4 | 4 | PASS | [test_results.md](../../exercises/10.K5-dr4-vs-fr4/outputs/expected/test_results.md) |
| 10.K6-cmis-dom-quantities | 4 | PASS | [test_results.md](../../exercises/10.K6-cmis-dom-quantities/outputs/expected/test_results.md) |
| 10.K7-miscabled-uplink-capacity | 4 | PASS | [test_results.md](../../exercises/10.K7-miscabled-uplink-capacity/outputs/expected/test_results.md) |
| 10.M1-link-commissioning-checklist | 4 | PASS | [test_results.md](../../exercises/10.M1-link-commissioning-checklist/outputs/expected/test_results.md) |
| 10.M2-physical-or-higher-layer | 4 | PASS | [test_results.md](../../exercises/10.M2-physical-or-higher-layer/outputs/expected/test_results.md) |
| 10.M3-small-fabric-bom-spares | 4 | PASS | [test_results.md](../../exercises/10.M3-small-fabric-bom-spares/outputs/expected/test_results.md) |
| 10.M4-runbook-cabling-schedule | 4 | PASS | [test_results.md](../../exercises/10.M4-runbook-cabling-schedule/outputs/expected/test_results.md) |
| 10.R1-fec-independence-violations | 4 | PASS | [test_results.md](../../exercises/10.R1-fec-independence-violations/outputs/expected/test_results.md) |
| 10.R2-real-warning-thresholds | 4 | PASS | [test_results.md](../../exercises/10.R2-real-warning-thresholds/outputs/expected/test_results.md) |
| 10.R3-l1-vs-l3-limits | 4 | PASS | [test_results.md](../../exercises/10.R3-l1-vs-l3-limits/outputs/expected/test_results.md) |
| 10.R4-two-snapshot-blind-spots | 4 | PASS | [test_results.md](../../exercises/10.R4-two-snapshot-blind-spots/outputs/expected/test_results.md) |
| 10.T1-leaf-r6-uplinks-dirty | 4 | PASS | [test_results.md](../../exercises/10.T1-leaf-r6-uplinks-dirty/outputs/expected/test_results.md) |
| 10.W1-cross-hall-link-budget | 4 | PASS | [test_results.md](../../exercises/10.W1-cross-hall-link-budget/outputs/expected/test_results.md) |
| 10.W2-fec-arithmetic-sparing | 4 | PASS | [test_results.md](../../exercises/10.W2-fec-arithmetic-sparing/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
