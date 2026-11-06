# Test results: ch05

**PASS**: 90 passed, 0 skipped, 90 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 1.118 |
| `test_lab_starter_fails_gracefully` | PASS | 0.628 |
| `test_lab_runs_without_generator` | PASS | 1.929 |
| `test_lab_golden_solution_report` | PASS | 0.003 |
| `test_lab_golden_starter_report` | PASS | 0.705 |
| `test_exercise_index` | PASS | 0.076 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 5.1-bdf-vs-slot | 4 | PASS | [test_results.md](../../exercises/5.1-bdf-vs-slot/outputs/expected/test_results.md) |
| 5.10-lab-topology-mapper | 4 | PASS | [test_results.md](../../exercises/5.10-lab-topology-mapper/outputs/expected/test_results.md) |
| 5.11-shortest-gpu-nic-pairings | 4 | PASS | [test_results.md](../../exercises/5.11-shortest-gpu-nic-pairings/outputs/expected/test_results.md) |
| 5.12-p2p-vs-host-staged | 4 | PASS | [test_results.md](../../exercises/5.12-p2p-vs-host-staged/outputs/expected/test_results.md) |
| 5.13-rank-placement-validation | 4 | PASS | [test_results.md](../../exercises/5.13-rank-placement-validation/outputs/expected/test_results.md) |
| 5.14-section-20-4-lab | 4 | PASS | [test_results.md](../../exercises/5.14-section-20-4-lab/outputs/expected/test_results.md) |
| 5.15-prove-gdr | 4 | PASS | [test_results.md](../../exercises/5.15-prove-gdr/outputs/expected/test_results.md) |
| 5.16-rail-swap-after-rack-move | 4 | PASS | [test_results.md](../../exercises/5.16-rail-swap-after-rack-move/outputs/expected/test_results.md) |
| 5.17-four-nic-node-variant | 4 | PASS | [test_results.md](../../exercises/5.17-four-nic-node-variant/outputs/expected/test_results.md) |
| 5.18-raw-derived-modeled | 4 | PASS | [test_results.md](../../exercises/5.18-raw-derived-modeled/outputs/expected/test_results.md) |
| 5.19-time-correlated-slow-paths | 4 | PASS | [test_results.md](../../exercises/5.19-time-correlated-slow-paths/outputs/expected/test_results.md) |
| 5.2-topo-legend-ordering | 4 | PASS | [test_results.md](../../exercises/5.2-topo-legend-ordering/outputs/expected/test_results.md) |
| 5.20-uuid-bdf-keys | 4 | PASS | [test_results.md](../../exercises/5.20-uuid-bdf-keys/outputs/expected/test_results.md) |
| 5.21-lstopo-vs-nvidia-smi | 4 | PASS | [test_results.md](../../exercises/5.21-lstopo-vs-nvidia-smi/outputs/expected/test_results.md) |
| 5.3-hca-index-vs-rail | 4 | PASS | [test_results.md](../../exercises/5.3-hca-index-vs-rail/outputs/expected/test_results.md) |
| 5.4-nv18-nvswitch | 4 | PASS | [test_results.md](../../exercises/5.4-nv18-nvswitch/outputs/expected/test_results.md) |
| 5.5-acs-redirect | 4 | PASS | [test_results.md](../../exercises/5.5-acs-redirect/outputs/expected/test_results.md) |
| 5.6-gdr-prerequisites | 4 | PASS | [test_results.md](../../exercises/5.6-gdr-prerequisites/outputs/expected/test_results.md) |
| 5.7-numa-local-resources | 4 | PASS | [test_results.md](../../exercises/5.7-numa-local-resources/outputs/expected/test_results.md) |
| 5.8-pcie-budget | 4 | PASS | [test_results.md](../../exercises/5.8-pcie-budget/outputs/expected/test_results.md) |
| 5.9-one-bad-path-cost | 4 | PASS | [test_results.md](../../exercises/5.9-one-bad-path-cost/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
