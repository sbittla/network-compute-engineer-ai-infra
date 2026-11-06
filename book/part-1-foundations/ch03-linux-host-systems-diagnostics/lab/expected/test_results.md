# Test results: ch03

**PASS**: 74 passed, 0 skipped, 74 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.289 |
| `test_lab_starter_fails_gracefully` | PASS | 0.224 |
| `test_lab_runs_without_generator` | PASS | 1.018 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 0.268 |
| `test_exercise_index` | PASS | 0.036 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 3.1-reading-the-cpu-map | 4 | PASS | [test_results.md](../../exercises/3.1-reading-the-cpu-map/outputs/expected/test_results.md) |
| 3.10-queues-stripes-packets | 4 | PASS | [test_results.md](../../exercises/3.10-queues-stripes-packets/outputs/expected/test_results.md) |
| 3.11-host-collector-lab | 4 | PASS | [test_results.md](../../exercises/3.11-host-collector-lab/outputs/expected/test_results.md) |
| 3.12-host-inventory-snapshot | 4 | PASS | [test_results.md](../../exercises/3.12-host-inventory-snapshot/outputs/expected/test_results.md) |
| 3.13-host-health-orion-xl | 4 | PASS | [test_results.md](../../exercises/3.13-host-health-orion-xl/outputs/expected/test_results.md) |
| 3.14-simulated-data-blind-spots | 4 | PASS | [test_results.md](../../exercises/3.14-simulated-data-blind-spots/outputs/expected/test_results.md) |
| 3.15-healthy-with-check-gaps | 4 | PASS | [test_results.md](../../exercises/3.15-healthy-with-check-gaps/outputs/expected/test_results.md) |
| 3.16-pcie-cost-upper-bound | 4 | PASS | [test_results.md](../../exercises/3.16-pcie-cost-upper-bound/outputs/expected/test_results.md) |
| 3.17-baseline-threshold-argument | 4 | PASS | [test_results.md](../../exercises/3.17-baseline-threshold-argument/outputs/expected/test_results.md) |
| 3.2-since-boot-samples | 4 | PASS | [test_results.md](../../exercises/3.2-since-boot-samples/outputs/expected/test_results.md) |
| 3.3-diluted-signals | 4 | PASS | [test_results.md](../../exercises/3.3-diluted-signals/outputs/expected/test_results.md) |
| 3.4-pcie-status-lines | 4 | PASS | [test_results.md](../../exercises/3.4-pcie-status-lines/outputs/expected/test_results.md) |
| 3.5-corrected-vs-uncorrected | 4 | PASS | [test_results.md](../../exercises/3.5-corrected-vs-uncorrected/outputs/expected/test_results.md) |
| 3.6-numa-and-utilization | 4 | PASS | [test_results.md](../../exercises/3.6-numa-and-utilization/outputs/expected/test_results.md) |
| 3.7-safe-collection | 4 | PASS | [test_results.md](../../exercises/3.7-safe-collection/outputs/expected/test_results.md) |
| 3.8-cpu-low-throughput-poor | 4 | PASS | [test_results.md](../../exercises/3.8-cpu-low-throughput-poor/outputs/expected/test_results.md) |
| 3.9-narrower-pcie-pipe | 4 | PASS | [test_results.md](../../exercises/3.9-narrower-pcie-pipe/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
