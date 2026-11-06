# Test results: ch15

**PASS**: 98 passed, 0 skipped, 98 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.785 |
| `test_lab_starter_fails_gracefully` | PASS | 0.666 |
| `test_lab_runs_without_generator` | PASS | 1.464 |
| `test_lab_golden_solution_report` | PASS | 0.005 |
| `test_lab_golden_starter_report` | PASS | 0.659 |
| `test_exercise_index` | PASS | 0.097 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| D1-rag-serving-tier | 4 | PASS | [test_results.md](../../exercises/D1-rag-serving-tier/outputs/expected/test_results.md) |
| DEL-capacity-model-memo | 4 | PASS | [test_results.md](../../exercises/DEL-capacity-model-memo/outputs/expected/test_results.md) |
| K1-decode-memory-bound | 4 | PASS | [test_results.md](../../exercises/K1-decode-memory-bound/outputs/expected/test_results.md) |
| K2-latency-metrics | 4 | PASS | [test_results.md](../../exercises/K2-latency-metrics/outputs/expected/test_results.md) |
| K3-paged-kv-cache | 4 | PASS | [test_results.md](../../exercises/K3-paged-kv-cache/outputs/expected/test_results.md) |
| K4-batching-strategies | 4 | PASS | [test_results.md](../../exercises/K4-batching-strategies/outputs/expected/test_results.md) |
| K5-goodput | 4 | PASS | [test_results.md](../../exercises/K5-goodput/outputs/expected/test_results.md) |
| K6-gqa-kv-bytes | 4 | PASS | [test_results.md](../../exercises/K6-gqa-kv-bytes/outputs/expected/test_results.md) |
| K7-gpu-utilization-decode | 4 | PASS | [test_results.md](../../exercises/K7-gpu-utilization-decode/outputs/expected/test_results.md) |
| K8-recompute-vs-swap | 4 | PASS | [test_results.md](../../exercises/K8-recompute-vs-swap/outputs/expected/test_results.md) |
| L1-serving-lab | 4 | PASS | [test_results.md](../../exercises/L1-serving-lab/outputs/expected/test_results.md) |
| O1-memory-demand-table | 4 | PASS | [test_results.md](../../exercises/O1-memory-demand-table/outputs/expected/test_results.md) |
| O2-analyze-serving-trace | 4 | PASS | [test_results.md](../../exercises/O2-analyze-serving-trace/outputs/expected/test_results.md) |
| O3-compare-serving-configs | 4 | PASS | [test_results.md](../../exercises/O3-compare-serving-configs/outputs/expected/test_results.md) |
| O4-prompt-split-8k | 4 | PASS | [test_results.md](../../exercises/O4-prompt-split-8k/outputs/expected/test_results.md) |
| O5-speculative-decoding | 4 | PASS | [test_results.md](../../exercises/O5-speculative-decoding/outputs/expected/test_results.md) |
| R1-capacity-model-assumptions | 4 | PASS | [test_results.md](../../exercises/R1-capacity-model-assumptions/outputs/expected/test_results.md) |
| R2-sampled-itl-p999 | 4 | PASS | [test_results.md](../../exercises/R2-sampled-itl-p999/outputs/expected/test_results.md) |
| R3-re-evaluate-disaggregation | 4 | PASS | [test_results.md](../../exercises/R3-re-evaluate-disaggregation/outputs/expected/test_results.md) |
| R4-fp8-kv-safety | 4 | PASS | [test_results.md](../../exercises/R4-fp8-kv-safety/outputs/expected/test_results.md) |
| T1-token-2-stall | 4 | PASS | [test_results.md](../../exercises/T1-token-2-stall/outputs/expected/test_results.md) |
| W1-long-context-tier-capacity | 4 | PASS | [test_results.md](../../exercises/W1-long-context-tier-capacity/outputs/expected/test_results.md) |
| W2-shared-pool-littles-law | 4 | PASS | [test_results.md](../../exercises/W2-shared-pool-littles-law/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
