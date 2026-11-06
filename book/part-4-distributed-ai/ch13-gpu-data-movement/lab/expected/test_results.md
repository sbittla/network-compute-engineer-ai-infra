# Test results: ch13

**PASS**: 78 passed, 0 skipped, 78 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.627 |
| `test_lab_starter_fails_gracefully` | PASS | 0.556 |
| `test_lab_runs_without_generator` | PASS | 1.029 |
| `test_lab_golden_solution_report` | PASS | 0.001 |
| `test_lab_golden_starter_report` | PASS | 0.690 |
| `test_exercise_index` | PASS | 0.081 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 13.1-nvlink-vs-nic-volume | 4 | PASS | [test_results.md](../../exercises/13.1-nvlink-vs-nic-volume/outputs/expected/test_results.md) |
| 13.10-gpu-low-network-high | 4 | PASS | [test_results.md](../../exercises/13.10-gpu-low-network-high/outputs/expected/test_results.md) |
| 13.11-validate-gdr-locality | 4 | PASS | [test_results.md](../../exercises/13.11-validate-gdr-locality/outputs/expected/test_results.md) |
| 13.12-straggler-diagnosis-lab | 4 | PASS | [test_results.md](../../exercises/13.12-straggler-diagnosis-lab/outputs/expected/test_results.md) |
| 13.13-slow-node-tp-job | 4 | PASS | [test_results.md](../../exercises/13.13-slow-node-tp-job/outputs/expected/test_results.md) |
| 13.14-straggler-telemetry-design | 4 | PASS | [test_results.md](../../exercises/13.14-straggler-telemetry-design/outputs/expected/test_results.md) |
| 13.15-busy-network-not-bottleneck | 4 | PASS | [test_results.md](../../exercises/13.15-busy-network-not-bottleneck/outputs/expected/test_results.md) |
| 13.16-validate-against-maximum | 4 | PASS | [test_results.md](../../exercises/13.16-validate-against-maximum/outputs/expected/test_results.md) |
| 13.17-simulated-telemetry-limits | 4 | PASS | [test_results.md](../../exercises/13.17-simulated-telemetry-limits/outputs/expected/test_results.md) |
| 13.18-locality-mistakes-production | 4 | PASS | [test_results.md](../../exercises/13.18-locality-mistakes-production/outputs/expected/test_results.md) |
| 13.2-gdr-prerequisites | 4 | PASS | [test_results.md](../../exercises/13.2-gdr-prerequisites/outputs/expected/test_results.md) |
| 13.3-topology-labels | 4 | PASS | [test_results.md](../../exercises/13.3-topology-labels/outputs/expected/test_results.md) |
| 13.4-gpu-util-misleads | 4 | PASS | [test_results.md](../../exercises/13.4-gpu-util-misleads/outputs/expected/test_results.md) |
| 13.5-overlap-window | 4 | PASS | [test_results.md](../../exercises/13.5-overlap-window/outputs/expected/test_results.md) |
| 13.6-correlated-retransmissions | 4 | PASS | [test_results.md](../../exercises/13.6-correlated-retransmissions/outputs/expected/test_results.md) |
| 13.7-pipeline-message-paths | 4 | PASS | [test_results.md](../../exercises/13.7-pipeline-message-paths/outputs/expected/test_results.md) |
| 13.8-straggler-amplification | 4 | PASS | [test_results.md](../../exercises/13.8-straggler-amplification/outputs/expected/test_results.md) |
| 13.9-trace-communication-path | 4 | PASS | [test_results.md](../../exercises/13.9-trace-communication-path/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
