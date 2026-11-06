# Test results: ch12

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.694 |
| `test_lab_starter_fails_gracefully` | PASS | 0.571 |
| `test_lab_runs_without_generator` | PASS | 1.301 |
| `test_lab_golden_solution_report` | PASS | 0.004 |
| `test_lab_golden_starter_report` | PASS | 0.628 |
| `test_exercise_index` | PASS | 0.065 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 12.1-reduce-scatter-all-gather | 4 | PASS | [test_results.md](../../exercises/12.1-reduce-scatter-all-gather/outputs/expected/test_results.md) |
| 12.10-o1-collectives-by-hand | 4 | PASS | [test_results.md](../../exercises/12.10-o1-collectives-by-hand/outputs/expected/test_results.md) |
| 12.11-o2-analyze-result-set | 4 | PASS | [test_results.md](../../exercises/12.11-o2-analyze-result-set/outputs/expected/test_results.md) |
| 12.12-o3-two-rank-mappings | 4 | PASS | [test_results.md](../../exercises/12.12-o3-two-rank-mappings/outputs/expected/test_results.md) |
| 12.13-nccl-tests-analysis-lab | 4 | PASS | [test_results.md](../../exercises/12.13-nccl-tests-analysis-lab/outputs/expected/test_results.md) |
| 12.14-latency-doubled-bandwidth-fine | 4 | PASS | [test_results.md](../../exercises/12.14-latency-doubled-bandwidth-fine/outputs/expected/test_results.md) |
| 12.15-orion-acceptance-suite | 4 | PASS | [test_results.md](../../exercises/12.15-orion-acceptance-suite/outputs/expected/test_results.md) |
| 12.16-avg-bus-bandwidth | 4 | PASS | [test_results.md](../../exercises/12.16-avg-bus-bandwidth/outputs/expected/test_results.md) |
| 12.17-simulation-blind-spots | 4 | PASS | [test_results.md](../../exercises/12.17-simulation-blind-spots/outputs/expected/test_results.md) |
| 12.18-misalignment-in-production | 4 | PASS | [test_results.md](../../exercises/12.18-misalignment-in-production/outputs/expected/test_results.md) |
| 12.19-nccl-log-as-evidence | 4 | PASS | [test_results.md](../../exercises/12.19-nccl-log-as-evidence/outputs/expected/test_results.md) |
| 12.2-why-all-to-all-is-harder | 4 | PASS | [test_results.md](../../exercises/12.2-why-all-to-all-is-harder/outputs/expected/test_results.md) |
| 12.20-alltoall-pxn | 4 | PASS | [test_results.md](../../exercises/12.20-alltoall-pxn/outputs/expected/test_results.md) |
| 12.3-busbw-factors-n16 | 4 | PASS | [test_results.md](../../exercises/12.3-busbw-factors-n16/outputs/expected/test_results.md) |
| 12.4-ll-ll128-simple | 4 | PASS | [test_results.md](../../exercises/12.4-ll-ll128-simple/outputs/expected/test_results.md) |
| 12.5-nccl-channels | 4 | PASS | [test_results.md](../../exercises/12.5-nccl-channels/outputs/expected/test_results.md) |
| 12.6-nccl-environment-variables | 4 | PASS | [test_results.md](../../exercises/12.6-nccl-environment-variables/outputs/expected/test_results.md) |
| 12.7-impossible-2000-gbps | 4 | PASS | [test_results.md](../../exercises/12.7-impossible-2000-gbps/outputs/expected/test_results.md) |
| 12.8-rows-to-bandwidth | 4 | PASS | [test_results.md](../../exercises/12.8-rows-to-bandwidth/outputs/expected/test_results.md) |
| 12.9-buckets-alpha-beta | 4 | PASS | [test_results.md](../../exercises/12.9-buckets-alpha-beta/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
