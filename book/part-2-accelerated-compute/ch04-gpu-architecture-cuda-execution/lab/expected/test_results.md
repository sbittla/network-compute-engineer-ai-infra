# Test results: ch04

**PASS**: 82 passed, 0 skipped, 82 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.884 |
| `test_lab_starter_fails_gracefully` | PASS | 0.558 |
| `test_lab_runs_without_generator` | PASS | 1.371 |
| `test_lab_golden_solution_report` | PASS | 0.001 |
| `test_lab_golden_starter_report` | PASS | 0.635 |
| `test_exercise_index` | PASS | 0.081 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 4.1-sm-warp-block-grid | 4 | PASS | [test_results.md](../../exercises/4.1-sm-warp-block-grid/outputs/expected/test_results.md) |
| 4.10-lab-trace-analysis | 4 | PASS | [test_results.md](../../exercises/4.10-lab-trace-analysis/outputs/expected/test_results.md) |
| 4.11-trace-matmul-end-to-end | 4 | PASS | [test_results.md](../../exercises/4.11-trace-matmul-end-to-end/outputs/expected/test_results.md) |
| 4.12-bottleneck-classes-from-trace | 4 | PASS | [test_results.md](../../exercises/4.12-bottleneck-classes-from-trace/outputs/expected/test_results.md) |
| 4.13-waves-layout-intensity | 4 | PASS | [test_results.md](../../exercises/4.13-waves-layout-intensity/outputs/expected/test_results.md) |
| 4.14-p99-allocator-churn | 4 | PASS | [test_results.md](../../exercises/4.14-p99-allocator-churn/outputs/expected/test_results.md) |
| 4.15-input-step-overhead-design | 4 | PASS | [test_results.md](../../exercises/4.15-input-step-overhead-design/outputs/expected/test_results.md) |
| 4.16-evidence-labels-worked-example | 4 | PASS | [test_results.md](../../exercises/4.16-evidence-labels-worked-example/outputs/expected/test_results.md) |
| 4.17-gap-classifier-calibration | 4 | PASS | [test_results.md](../../exercises/4.17-gap-classifier-calibration/outputs/expected/test_results.md) |
| 4.18-single-gpu-trace-limits | 4 | PASS | [test_results.md](../../exercises/4.18-single-gpu-trace-limits/outputs/expected/test_results.md) |
| 4.19-prioritization-by-cost | 4 | PASS | [test_results.md](../../exercises/4.19-prioritization-by-cost/outputs/expected/test_results.md) |
| 4.2-coalescing-sector-counts | 4 | PASS | [test_results.md](../../exercises/4.2-coalescing-sector-counts/outputs/expected/test_results.md) |
| 4.3-implicit-sync-patterns | 4 | PASS | [test_results.md](../../exercises/4.3-implicit-sync-patterns/outputs/expected/test_results.md) |
| 4.4-pageable-vs-pinned-copies | 4 | PASS | [test_results.md](../../exercises/4.4-pageable-vs-pinned-copies/outputs/expected/test_results.md) |
| 4.5-gpu-util-meaning | 4 | PASS | [test_results.md](../../exercises/4.5-gpu-util-meaning/outputs/expected/test_results.md) |
| 4.6-nvtx-cpu-side-ranges | 4 | PASS | [test_results.md](../../exercises/4.6-nvtx-cpu-side-ranges/outputs/expected/test_results.md) |
| 4.7-occupancy-latency-hiding | 4 | PASS | [test_results.md](../../exercises/4.7-occupancy-latency-hiding/outputs/expected/test_results.md) |
| 4.8-occupancy-bytes-in-flight | 4 | PASS | [test_results.md](../../exercises/4.8-occupancy-bytes-in-flight/outputs/expected/test_results.md) |
| 4.9-launch-bound-copy-cost | 4 | PASS | [test_results.md](../../exercises/4.9-launch-bound-copy-cost/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
