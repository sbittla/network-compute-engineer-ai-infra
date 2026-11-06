# Test results: ch22

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 1.316 |
| `test_lab_starter_fails_gracefully` | PASS | 0.937 |
| `test_lab_runs_without_generator` | PASS | 1.744 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 0.954 |
| `test_exercise_index` | PASS | 0.049 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| D1-continuous-regression-detection | 4 | PASS | [test_results.md](../../exercises/D1-continuous-regression-detection/outputs/expected/test_results.md) |
| K1-step-time-equation | 4 | PASS | [test_results.md](../../exercises/K1-step-time-equation/outputs/expected/test_results.md) |
| K2-gpu-utilization-misleads | 4 | PASS | [test_results.md](../../exercises/K2-gpu-utilization-misleads/outputs/expected/test_results.md) |
| K3-mean-vs-median | 4 | PASS | [test_results.md](../../exercises/K3-mean-vs-median/outputs/expected/test_results.md) |
| K4-discriminating-test | 4 | PASS | [test_results.md](../../exercises/K4-discriminating-test/outputs/expected/test_results.md) |
| K5-period-indicator-role | 4 | PASS | [test_results.md](../../exercises/K5-period-indicator-role/outputs/expected/test_results.md) |
| K6-weak-strong-scaling | 4 | PASS | [test_results.md](../../exercises/K6-weak-strong-scaling/outputs/expected/test_results.md) |
| K7-survivorship-bias | 4 | PASS | [test_results.md](../../exercises/K7-survivorship-bias/outputs/expected/test_results.md) |
| K8-rollback-as-diagnostic | 4 | PASS | [test_results.md](../../exercises/K8-rollback-as-diagnostic/outputs/expected/test_results.md) |
| L1-attribute-regression-lab | 4 | PASS | [test_results.md](../../exercises/L1-attribute-regression-lab/outputs/expected/test_results.md) |
| O1-investigate-end-to-end | 4 | PASS | [test_results.md](../../exercises/O1-investigate-end-to-end/outputs/expected/test_results.md) |
| O2-hypothesis-tree-ranking | 4 | PASS | [test_results.md](../../exercises/O2-hypothesis-tree-ranking/outputs/expected/test_results.md) |
| O3-before-after-report | 4 | PASS | [test_results.md](../../exercises/O3-before-after-report/outputs/expected/test_results.md) |
| R1-unattributed-common-shift | 4 | PASS | [test_results.md](../../exercises/R1-unattributed-common-shift/outputs/expected/test_results.md) |
| R2-high-r2-not-causal | 4 | PASS | [test_results.md](../../exercises/R2-high-r2-not-causal/outputs/expected/test_results.md) |
| R3-excluding-failed-jobs | 4 | PASS | [test_results.md](../../exercises/R3-excluding-failed-jobs/outputs/expected/test_results.md) |
| R4-gdr-evidence-gap | 4 | PASS | [test_results.md](../../exercises/R4-gdr-evidence-gap/outputs/expected/test_results.md) |
| T1-periodic-stalls-full-run | 4 | PASS | [test_results.md](../../exercises/T1-periodic-stalls-full-run/outputs/expected/test_results.md) |
| W1-attribution-with-interaction | 4 | PASS | [test_results.md](../../exercises/W1-attribution-with-interaction/outputs/expected/test_results.md) |
| W2-scaling-and-detectability | 4 | PASS | [test_results.md](../../exercises/W2-scaling-and-detectability/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
