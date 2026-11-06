# Test results: ch18

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 2.185 |
| `test_lab_starter_fails_gracefully` | PASS | 1.894 |
| `test_lab_runs_without_generator` | PASS | 1.920 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 1.766 |
| `test_exercise_index` | PASS | 0.069 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| D1-orion-xl-alerting | 4 | PASS | [test_results.md](../../exercises/D1-orion-xl-alerting/outputs/expected/test_results.md) |
| K1-lying-utilization-metric | 4 | PASS | [test_results.md](../../exercises/K1-lying-utilization-metric/outputs/expected/test_results.md) |
| K2-polling-at-400g | 4 | PASS | [test_results.md](../../exercises/K2-polling-at-400g/outputs/expected/test_results.md) |
| K3-throughput-vs-goodput | 4 | PASS | [test_results.md](../../exercises/K3-throughput-vs-goodput/outputs/expected/test_results.md) |
| K4-two-window-alerts | 4 | PASS | [test_results.md](../../exercises/K4-two-window-alerts/outputs/expected/test_results.md) |
| K5-pause-direction | 4 | PASS | [test_results.md](../../exercises/K5-pause-direction/outputs/expected/test_results.md) |
| K6-incident-roles | 4 | PASS | [test_results.md](../../exercises/K6-incident-roles/outputs/expected/test_results.md) |
| K7-timeline-arithmetic | 4 | PASS | [test_results.md](../../exercises/K7-timeline-arithmetic/outputs/expected/test_results.md) |
| K8-label-cardinality | 4 | PASS | [test_results.md](../../exercises/K8-label-cardinality/outputs/expected/test_results.md) |
| L1-telemetry-forensics-lab | 4 | PASS | [test_results.md](../../exercises/L1-telemetry-forensics-lab/outputs/expected/test_results.md) |
| M1-sli-slo-specification | 4 | PASS | [test_results.md](../../exercises/M1-sli-slo-specification/outputs/expected/test_results.md) |
| M2-dashboard-hierarchy | 4 | PASS | [test_results.md](../../exercises/M2-dashboard-hierarchy/outputs/expected/test_results.md) |
| M3-incident-timeline-postmortem | 4 | PASS | [test_results.md](../../exercises/M3-incident-timeline-postmortem/outputs/expected/test_results.md) |
| R1-proven-vs-correlated | 4 | PASS | [test_results.md](../../exercises/R1-proven-vs-correlated/outputs/expected/test_results.md) |
| R2-switch-telemetry-resolution | 4 | PASS | [test_results.md](../../exercises/R2-switch-telemetry-resolution/outputs/expected/test_results.md) |
| R3-gaming-throughput-sli | 4 | PASS | [test_results.md](../../exercises/R3-gaming-throughput-sli/outputs/expected/test_results.md) |
| R4-blameless-evidence | 4 | PASS | [test_results.md](../../exercises/R4-blameless-evidence/outputs/expected/test_results.md) |
| T1-ttft-page | 4 | PASS | [test_results.md](../../exercises/T1-ttft-page/outputs/expected/test_results.md) |
| W1-error-budget-burn-rate | 4 | PASS | [test_results.md](../../exercises/W1-error-budget-burn-rate/outputs/expected/test_results.md) |
| W2-regression-page-worth | 4 | PASS | [test_results.md](../../exercises/W2-regression-page-worth/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
