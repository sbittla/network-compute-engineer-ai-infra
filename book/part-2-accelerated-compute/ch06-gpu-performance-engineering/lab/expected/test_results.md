# Test results: ch06

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 2.878 |
| `test_lab_starter_fails_gracefully` | PASS | 0.602 |
| `test_lab_runs_without_generator` | PASS | 5.058 |
| `test_lab_golden_solution_report` | PASS | 0.003 |
| `test_lab_golden_starter_report` | PASS | 0.602 |
| `test_exercise_index` | PASS | 0.041 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 6.1-intensity-ridge-points | 4 | PASS | [test_results.md](../../exercises/6.1-intensity-ridge-points/outputs/expected/test_results.md) |
| 6.10-lab-benchmark-harness | 4 | PASS | [test_results.md](../../exercises/6.10-lab-benchmark-harness/outputs/expected/test_results.md) |
| 6.11-roofline-supplied-data | 4 | PASS | [test_results.md](../../exercises/6.11-roofline-supplied-data/outputs/expected/test_results.md) |
| 6.12-nccl-benchmark-protocol | 4 | PASS | [test_results.md](../../exercises/6.12-nccl-benchmark-protocol/outputs/expected/test_results.md) |
| 6.13-is-the-improvement-real | 4 | PASS | [test_results.md](../../exercises/6.13-is-the-improvement-real/outputs/expected/test_results.md) |
| 6.14-gelu-microbenchmark-gap | 4 | PASS | [test_results.md](../../exercises/6.14-gelu-microbenchmark-gap/outputs/expected/test_results.md) |
| 6.15-nightly-regression-gate | 4 | PASS | [test_results.md](../../exercises/6.15-nightly-regression-gate/outputs/expected/test_results.md) |
| 6.16-laptop-noise-manifest | 4 | PASS | [test_results.md](../../exercises/6.16-laptop-noise-manifest/outputs/expected/test_results.md) |
| 6.17-cliffs-delta-levels | 4 | PASS | [test_results.md](../../exercises/6.17-cliffs-delta-levels/outputs/expected/test_results.md) |
| 6.18-power-cap-rebaseline | 4 | PASS | [test_results.md](../../exercises/6.18-power-cap-rebaseline/outputs/expected/test_results.md) |
| 6.19-serving-slo-protocol | 4 | PASS | [test_results.md](../../exercises/6.19-serving-slo-protocol/outputs/expected/test_results.md) |
| 6.2-gbps-vs-tflops | 4 | PASS | [test_results.md](../../exercises/6.2-gbps-vs-tflops/outputs/expected/test_results.md) |
| 6.20-keep-a3-recompute | 4 | PASS | [test_results.md](../../exercises/6.20-keep-a3-recompute/outputs/expected/test_results.md) |
| 6.3-impossible-dram-bandwidth | 4 | PASS | [test_results.md](../../exercises/6.3-impossible-dram-bandwidth/outputs/expected/test_results.md) |
| 6.4-mfu-vs-hfu | 4 | PASS | [test_results.md](../../exercises/6.4-mfu-vs-hfu/outputs/expected/test_results.md) |
| 6.5-variation-sources-controls | 4 | PASS | [test_results.md](../../exercises/6.5-variation-sources-controls/outputs/expected/test_results.md) |
| 6.6-run-unit-of-replication | 4 | PASS | [test_results.md](../../exercises/6.6-run-unit-of-replication/outputs/expected/test_results.md) |
| 6.7-clocks-event-reasons | 4 | PASS | [test_results.md](../../exercises/6.7-clocks-event-reasons/outputs/expected/test_results.md) |
| 6.8-intensity-batch-size | 4 | PASS | [test_results.md](../../exercises/6.8-intensity-batch-size/outputs/expected/test_results.md) |
| 6.9-mfu-worked | 4 | PASS | [test_results.md](../../exercises/6.9-mfu-worked/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
