# Test results: ch11

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.625 |
| `test_lab_starter_fails_gracefully` | PASS | 0.581 |
| `test_lab_runs_without_generator` | PASS | 1.088 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 0.575 |
| `test_exercise_index` | PASS | 0.034 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 11.1-collectives-per-strategy | 4 | PASS | [test_results.md](../../exercises/11.1-collectives-per-strategy/outputs/expected/test_results.md) |
| 11.10-o1-choose-parallelism | 4 | PASS | [test_results.md](../../exercises/11.10-o1-choose-parallelism/outputs/expected/test_results.md) |
| 11.11-o2-step-time-sensitivity | 4 | PASS | [test_results.md](../../exercises/11.11-o2-step-time-sensitivity/outputs/expected/test_results.md) |
| 11.12-o3-failure-aware-workflow | 4 | PASS | [test_results.md](../../exercises/11.12-o3-failure-aware-workflow/outputs/expected/test_results.md) |
| 11.13-step-time-memory-lab | 4 | PASS | [test_results.md](../../exercises/11.13-step-time-memory-lab/outputs/expected/test_results.md) |
| 11.14-the-quiet-8-percent | 4 | PASS | [test_results.md](../../exercises/11.14-the-quiet-8-percent/outputs/expected/test_results.md) |
| 11.15-8k-sequences-layout | 4 | PASS | [test_results.md](../../exercises/11.15-8k-sequences-layout/outputs/expected/test_results.md) |
| 11.16-measure-assumptions-first | 4 | PASS | [test_results.md](../../exercises/11.16-measure-assumptions-first/outputs/expected/test_results.md) |
| 11.17-when-dp-matters | 4 | PASS | [test_results.md](../../exercises/11.17-when-dp-matters/outputs/expected/test_results.md) |
| 11.18-fits-80gb-insufficient | 4 | PASS | [test_results.md](../../exercises/11.18-fits-80gb-insufficient/outputs/expected/test_results.md) |
| 11.19-non-exponential-failures | 4 | PASS | [test_results.md](../../exercises/11.19-non-exponential-failures/outputs/expected/test_results.md) |
| 11.2-bytes-per-parameter | 4 | PASS | [test_results.md](../../exercises/11.2-bytes-per-parameter/outputs/expected/test_results.md) |
| 11.20-timeout-to-restart-tabletop | 4 | PASS | [test_results.md](../../exercises/11.20-timeout-to-restart-tabletop/outputs/expected/test_results.md) |
| 11.3-pipeline-bubble | 4 | PASS | [test_results.md](../../exercises/11.3-pipeline-bubble/outputs/expected/test_results.md) |
| 11.4-why-sequence-parallelism | 4 | PASS | [test_results.md](../../exercises/11.4-why-sequence-parallelism/outputs/expected/test_results.md) |
| 11.5-rail-locality-proof | 4 | PASS | [test_results.md](../../exercises/11.5-rail-locality-proof/outputs/expected/test_results.md) |
| 11.6-timeout-victim | 4 | PASS | [test_results.md](../../exercises/11.6-timeout-victim/outputs/expected/test_results.md) |
| 11.7-mfu-vs-recompute | 4 | PASS | [test_results.md](../../exercises/11.7-mfu-vs-recompute/outputs/expected/test_results.md) |
| 11.8-memory-audit | 4 | PASS | [test_results.md](../../exercises/11.8-memory-audit/outputs/expected/test_results.md) |
| 11.9-communication-budget | 4 | PASS | [test_results.md](../../exercises/11.9-communication-budget/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
