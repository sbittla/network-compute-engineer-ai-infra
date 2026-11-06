# Test results: ch23

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.719 |
| `test_lab_starter_fails_gracefully` | PASS | 0.698 |
| `test_lab_runs_without_generator` | PASS | 0.900 |
| `test_lab_golden_solution_report` | PASS | 0.001 |
| `test_lab_golden_starter_report` | PASS | 0.609 |
| `test_exercise_index` | PASS | 0.035 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| D1-grow-orion-384-gpus | 4 | PASS | [test_results.md](../../exercises/D1-grow-orion-384-gpus/outputs/expected/test_results.md) |
| K1-problem-statement-elements | 4 | PASS | [test_results.md](../../exercises/K1-problem-statement-elements/outputs/expected/test_results.md) |
| K2-register-owner-validation | 4 | PASS | [test_results.md](../../exercises/K2-register-owner-validation/outputs/expected/test_results.md) |
| K3-adr-revisit-trigger | 4 | PASS | [test_results.md](../../exercises/K3-adr-revisit-trigger/outputs/expected/test_results.md) |
| K4-rack-power-maximum | 4 | PASS | [test_results.md](../../exercises/K4-rack-power-maximum/outputs/expected/test_results.md) |
| K5-blast-radius-rack-vs-leaf | 4 | PASS | [test_results.md](../../exercises/K5-blast-radius-rack-vs-leaf/outputs/expected/test_results.md) |
| K6-fmea-detectability | 4 | PASS | [test_results.md](../../exercises/K6-fmea-detectability/outputs/expected/test_results.md) |
| K7-measured-label-at-l1 | 4 | PASS | [test_results.md](../../exercises/K7-measured-label-at-l1/outputs/expected/test_results.md) |
| K8-design-review-outcomes | 4 | PASS | [test_results.md](../../exercises/K8-design-review-outcomes/outputs/expected/test_results.md) |
| L1-design-review-linter | 4 | PASS | [test_results.md](../../exercises/L1-design-review-linter/outputs/expected/test_results.md) |
| M1-complete-capstone-track | 4 | PASS | [test_results.md](../../exercises/M1-complete-capstone-track/outputs/expected/test_results.md) |
| M2-conduct-design-review | 4 | PASS | [test_results.md](../../exercises/M2-conduct-design-review/outputs/expected/test_results.md) |
| M3-evidence-failure-backlog-talk | 4 | PASS | [test_results.md](../../exercises/M3-evidence-failure-backlog-talk/outputs/expected/test_results.md) |
| R1-highest-decision-value | 4 | PASS | [test_results.md](../../exercises/R1-highest-decision-value/outputs/expected/test_results.md) |
| R2-linter-blind-errors | 4 | PASS | [test_results.md](../../exercises/R2-linter-blind-errors/outputs/expected/test_results.md) |
| R3-correlated-failures | 4 | PASS | [test_results.md](../../exercises/R3-correlated-failures/outputs/expected/test_results.md) |
| R4-production-ready-evidence | 4 | PASS | [test_results.md](../../exercises/R4-production-ready-evidence/outputs/expected/test_results.md) |
| T1-contaminated-benchmark | 4 | PASS | [test_results.md](../../exercises/T1-contaminated-benchmark/outputs/expected/test_results.md) |
| W1-repair-kestrel-design | 4 | PASS | [test_results.md](../../exercises/W1-repair-kestrel-design/outputs/expected/test_results.md) |
| W2-checkpoint-interval-goodput | 4 | PASS | [test_results.md](../../exercises/W2-checkpoint-interval-goodput/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
