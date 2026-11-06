# Test results: ch21

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.796 |
| `test_lab_starter_fails_gracefully` | PASS | 0.730 |
| `test_lab_runs_without_generator` | PASS | 1.095 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 0.731 |
| `test_exercise_index` | PASS | 0.031 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| D1-inference-pool | 4 | PASS | [test_results.md](../../exercises/D1-inference-pool/outputs/expected/test_results.md) |
| K1-utilization-ladder | 4 | PASS | [test_results.md](../../exercises/K1-utilization-ladder/outputs/expected/test_results.md) |
| K2-usable-capacity | 4 | PASS | [test_results.md](../../exercises/K2-usable-capacity/outputs/expected/test_results.md) |
| K3-stranded-gpus | 4 | PASS | [test_results.md](../../exercises/K3-stranded-gpus/outputs/expected/test_results.md) |
| K4-plan-to-85-percent | 4 | PASS | [test_results.md](../../exercises/K4-plan-to-85-percent/outputs/expected/test_results.md) |
| K5-pue | 4 | PASS | [test_results.md](../../exercises/K5-pue/outputs/expected/test_results.md) |
| K6-2n-feeds | 4 | PASS | [test_results.md](../../exercises/K6-2n-feeds/outputs/expected/test_results.md) |
| K7-transients | 4 | PASS | [test_results.md](../../exercises/K7-transients/outputs/expected/test_results.md) |
| L1-lab21-capacity-model | 4 | PASS | [test_results.md](../../exercises/L1-lab21-capacity-model/outputs/expected/test_results.md) |
| M1-capacity-forecast | 4 | PASS | [test_results.md](../../exercises/M1-capacity-forecast/outputs/expected/test_results.md) |
| M2-two-designs | 4 | PASS | [test_results.md](../../exercises/M2-two-designs/outputs/expected/test_results.md) |
| M3-misleading-nominal-counts | 4 | PASS | [test_results.md](../../exercises/M3-misleading-nominal-counts/outputs/expected/test_results.md) |
| M4-power-cooling-guardrails | 4 | PASS | [test_results.md](../../exercises/M4-power-cooling-guardrails/outputs/expected/test_results.md) |
| R1-measure-not-assume | 4 | PASS | [test_results.md](../../exercises/R1-measure-not-assume/outputs/expected/test_results.md) |
| R2-break-even-paragraph | 4 | PASS | [test_results.md](../../exercises/R2-break-even-paragraph/outputs/expected/test_results.md) |
| R3-missing-tco-costs | 4 | PASS | [test_results.md](../../exercises/R3-missing-tco-costs/outputs/expected/test_results.md) |
| R4-facility-scheduler-signals | 4 | PASS | [test_results.md](../../exercises/R4-facility-scheduler-signals/outputs/expected/test_results.md) |
| T1-breaker-trip-job-start | 4 | PASS | [test_results.md](../../exercises/T1-breaker-trip-job-start/outputs/expected/test_results.md) |
| W1-tco-different-assumptions | 4 | PASS | [test_results.md](../../exercises/W1-tco-different-assumptions/outputs/expected/test_results.md) |
| W2-capping-tighter-hall | 4 | PASS | [test_results.md](../../exercises/W2-capping-tighter-hall/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
