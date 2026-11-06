# Test results: ch14

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.867 |
| `test_lab_starter_fails_gracefully` | PASS | 0.669 |
| `test_lab_runs_without_generator` | PASS | 2.062 |
| `test_lab_golden_solution_report` | PASS | 0.005 |
| `test_lab_golden_starter_report` | PASS | 0.693 |
| `test_exercise_index` | PASS | 0.080 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 14.1-littles-law-nvme | 4 | PASS | [test_results.md](../../exercises/14.1-littles-law-nvme/outputs/expected/test_results.md) |
| 14.10-interval-at-198h | 4 | PASS | [test_results.md](../../exercises/14.10-interval-at-198h/outputs/expected/test_results.md) |
| 14.11-storage-checkpoint-lab | 4 | PASS | [test_results.md](../../exercises/14.11-storage-checkpoint-lab/outputs/expected/test_results.md) |
| 14.12-resume-trained-worse | 4 | PASS | [test_results.md](../../exercises/14.12-resume-trained-worse/outputs/expected/test_results.md) |
| 14.13-orion-xl-checkpoint-strategy | 4 | PASS | [test_results.md](../../exercises/14.13-orion-xl-checkpoint-strategy/outputs/expected/test_results.md) |
| 14.14-uncertain-planner-inputs | 4 | PASS | [test_results.md](../../exercises/14.14-uncertain-planner-inputs/outputs/expected/test_results.md) |
| 14.15-simulated-trace-gaps | 4 | PASS | [test_results.md](../../exercises/14.15-simulated-trace-gaps/outputs/expected/test_results.md) |
| 14.16-interval-beyond-young | 4 | PASS | [test_results.md](../../exercises/14.16-interval-beyond-young/outputs/expected/test_results.md) |
| 14.17-missing-evidence | 4 | PASS | [test_results.md](../../exercises/14.17-missing-evidence/outputs/expected/test_results.md) |
| 14.18-io-plan-checkpoint-design | 4 | PASS | [test_results.md](../../exercises/14.18-io-plan-checkpoint-design/outputs/expected/test_results.md) |
| 14.19-checkpoint-benchmark-restore | 4 | PASS | [test_results.md](../../exercises/14.19-checkpoint-benchmark-restore/outputs/expected/test_results.md) |
| 14.2-metadata-vs-data-path | 4 | PASS | [test_results.md](../../exercises/14.2-metadata-vs-data-path/outputs/expected/test_results.md) |
| 14.20-per-directory-create-limit | 4 | PASS | [test_results.md](../../exercises/14.20-per-directory-create-limit/outputs/expected/test_results.md) |
| 14.3-checkpoint-contents | 4 | PASS | [test_results.md](../../exercises/14.3-checkpoint-contents/outputs/expected/test_results.md) |
| 14.4-blocking-vs-completion | 4 | PASS | [test_results.md](../../exercises/14.4-blocking-vs-completion/outputs/expected/test_results.md) |
| 14.5-commit-protocol | 4 | PASS | [test_results.md](../../exercises/14.5-commit-protocol/outputs/expected/test_results.md) |
| 14.6-recovery-vocabulary | 4 | PASS | [test_results.md](../../exercises/14.6-recovery-vocabulary/outputs/expected/test_results.md) |
| 14.7-tail-at-scale | 4 | PASS | [test_results.md](../../exercises/14.7-tail-at-scale/outputs/expected/test_results.md) |
| 14.8-checkpoint-size-rpo | 4 | PASS | [test_results.md](../../exercises/14.8-checkpoint-size-rpo/outputs/expected/test_results.md) |
| 14.9-metadata-vs-bandwidth-pipeline | 4 | PASS | [test_results.md](../../exercises/14.9-metadata-vs-bandwidth-pipeline/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
