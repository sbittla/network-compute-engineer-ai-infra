# Test results: ch01

**PASS**: 94 passed, 0 skipped, 94 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.429 |
| `test_lab_starter_fails_gracefully` | PASS | 0.371 |
| `test_lab_runs_without_generator` | PASS | 0.715 |
| `test_lab_golden_solution_report` | PASS | 0.001 |
| `test_lab_golden_starter_report` | PASS | 0.345 |
| `test_exercise_index` | PASS | 0.033 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 1.1-reference-architectures | 4 | PASS | [test_results.md](../../exercises/1.1-reference-architectures/outputs/expected/test_results.md) |
| 1.2-scale-up-vs-scale-out | 4 | PASS | [test_results.md](../../exercises/1.2-scale-up-vs-scale-out/outputs/expected/test_results.md) |
| 1.3-role-skill-matrix | 4 | PASS | [test_results.md](../../exercises/1.3-role-skill-matrix/outputs/expected/test_results.md) |
| DC-shared-vs-dedicated-inference | 4 | PASS | [test_results.md](../../exercises/DC-shared-vs-dedicated-inference/outputs/expected/test_results.md) |
| K1-cluster-vs-cloud-fleet | 4 | PASS | [test_results.md](../../exercises/K1-cluster-vs-cloud-fleet/outputs/expected/test_results.md) |
| K2-straggler-coupling | 4 | PASS | [test_results.md](../../exercises/K2-straggler-coupling/outputs/expected/test_results.md) |
| K3-bandwidth-conversions | 4 | PASS | [test_results.md](../../exercises/K3-bandwidth-conversions/outputs/expected/test_results.md) |
| K4-prefill-and-decode | 4 | PASS | [test_results.md](../../exercises/K4-prefill-and-decode/outputs/expected/test_results.md) |
| K5-allreduce-volume | 4 | PASS | [test_results.md](../../exercises/K5-allreduce-volume/outputs/expected/test_results.md) |
| K6-ceiling-fraction-readings | 4 | PASS | [test_results.md](../../exercises/K6-ceiling-fraction-readings/outputs/expected/test_results.md) |
| K7-gpu-utilization-metric | 4 | PASS | [test_results.md](../../exercises/K7-gpu-utilization-metric/outputs/expected/test_results.md) |
| LAB-workload-characterization | 4 | PASS | [test_results.md](../../exercises/LAB-workload-characterization/outputs/expected/test_results.md) |
| Q1-utilization-weak-evidence | 4 | PASS | [test_results.md](../../exercises/Q1-utilization-weak-evidence/outputs/expected/test_results.md) |
| Q2-impossible-nic-profile | 4 | PASS | [test_results.md](../../exercises/Q2-impossible-nic-profile/outputs/expected/test_results.md) |
| Q3-dp-traffic-stays-on-rail | 4 | PASS | [test_results.md](../../exercises/Q3-dp-traffic-stays-on-rail/outputs/expected/test_results.md) |
| R1-ceiling-model-limits | 4 | PASS | [test_results.md](../../exercises/R1-ceiling-model-limits/outputs/expected/test_results.md) |
| R2-job-posting-register | 4 | PASS | [test_results.md](../../exercises/R2-job-posting-register/outputs/expected/test_results.md) |
| R3-evidence-labels-worked-example | 4 | PASS | [test_results.md](../../exercises/R3-evidence-labels-worked-example/outputs/expected/test_results.md) |
| R4-dashboard-annotation | 4 | PASS | [test_results.md](../../exercises/R4-dashboard-annotation/outputs/expected/test_results.md) |
| TS-slow-replica-n29 | 4 | PASS | [test_results.md](../../exercises/TS-slow-replica-n29/outputs/expected/test_results.md) |
| WP1-repartition-w-train | 4 | PASS | [test_results.md](../../exercises/WP1-repartition-w-train/outputs/expected/test_results.md) |
| WP2-fp8-half-node-serving | 4 | PASS | [test_results.md](../../exercises/WP2-fp8-half-node-serving/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
