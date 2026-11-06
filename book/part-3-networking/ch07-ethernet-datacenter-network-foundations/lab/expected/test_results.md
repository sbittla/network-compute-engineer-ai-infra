# Test results: ch07

**PASS**: 78 passed, 0 skipped, 78 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.435 |
| `test_lab_starter_fails_gracefully` | PASS | 0.273 |
| `test_lab_runs_without_generator` | PASS | 0.641 |
| `test_lab_golden_solution_report` | PASS | 0.001 |
| `test_lab_golden_starter_report` | PASS | 0.368 |
| `test_exercise_index` | PASS | 0.025 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 7.D-parallel-links-spines | 4 | PASS | [test_results.md](../../exercises/7.D-parallel-links-spines/outputs/expected/test_results.md) |
| 7.K1-p2p-addressing | 4 | PASS | [test_results.md](../../exercises/7.K1-p2p-addressing/outputs/expected/test_results.md) |
| 7.K2-asn-design | 4 | PASS | [test_results.md](../../exercises/7.K2-asn-design/outputs/expected/test_results.md) |
| 7.K3-mtu-mismatch-bgp | 4 | PASS | [test_results.md](../../exercises/7.K3-mtu-mismatch-bgp/outputs/expected/test_results.md) |
| 7.K4-roce-frame-size | 4 | PASS | [test_results.md](../../exercises/7.K4-roce-frame-size/outputs/expected/test_results.md) |
| 7.K5-hash-polarization | 4 | PASS | [test_results.md](../../exercises/7.K5-hash-polarization/outputs/expected/test_results.md) |
| 7.K6-ecmp-link-failure | 4 | PASS | [test_results.md](../../exercises/7.K6-ecmp-link-failure/outputs/expected/test_results.md) |
| 7.K7-gray-failure-detection | 4 | PASS | [test_results.md](../../exercises/7.K7-gray-failure-detection/outputs/expected/test_results.md) |
| 7.K8-leaf-fault-domain | 4 | PASS | [test_results.md](../../exercises/7.K8-leaf-fault-domain/outputs/expected/test_results.md) |
| 7.L-fabric-design-lab | 4 | PASS | [test_results.md](../../exercises/7.L-fabric-design-lab/outputs/expected/test_results.md) |
| 7.O2-bgp-ecmp-routing-plan | 4 | PASS | [test_results.md](../../exercises/7.O2-bgp-ecmp-routing-plan/outputs/expected/test_results.md) |
| 7.R1-intent-validator-limits | 4 | PASS | [test_results.md](../../exercises/7.R1-intent-validator-limits/outputs/expected/test_results.md) |
| 7.R2-ecmp-model-assumptions | 4 | PASS | [test_results.md](../../exercises/7.R2-ecmp-model-assumptions/outputs/expected/test_results.md) |
| 7.R3-single-ping-rule | 4 | PASS | [test_results.md](../../exercises/7.R3-single-ping-rule/outputs/expected/test_results.md) |
| 7.R4-evidence-labels | 4 | PASS | [test_results.md](../../exercises/7.R4-evidence-labels/outputs/expected/test_results.md) |
| 7.T-bad-origin-troubleshooting | 4 | PASS | [test_results.md](../../exercises/7.T-bad-origin-troubleshooting/outputs/expected/test_results.md) |
| 7.W1-orion-384-design | 4 | PASS | [test_results.md](../../exercises/7.W1-orion-384-design/outputs/expected/test_results.md) |
| 7.W2-orion-384-failure-capacity | 4 | PASS | [test_results.md](../../exercises/7.W2-orion-384-failure-capacity/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
