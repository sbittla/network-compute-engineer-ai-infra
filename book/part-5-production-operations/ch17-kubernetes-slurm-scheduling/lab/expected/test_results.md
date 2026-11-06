# Test results: ch17

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.392 |
| `test_lab_starter_fails_gracefully` | PASS | 0.338 |
| `test_lab_runs_without_generator` | PASS | 0.629 |
| `test_lab_golden_solution_report` | PASS | 0.003 |
| `test_lab_golden_starter_report` | PASS | 0.377 |
| `test_exercise_index` | PASS | 0.028 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 17-D1-orion-xl-placement | 4 | PASS | [test_results.md](../../exercises/17-D1-orion-xl-placement/outputs/expected/test_results.md) |
| 17-DEL-placement-policy-guide | 4 | PASS | [test_results.md](../../exercises/17-DEL-placement-policy-guide/outputs/expected/test_results.md) |
| 17-K1-allocatable-seven-gpus | 4 | PASS | [test_results.md](../../exercises/17-K1-allocatable-seven-gpus/outputs/expected/test_results.md) |
| 17-K2-selector-vs-toleration | 4 | PASS | [test_results.md](../../exercises/17-K2-selector-vs-toleration/outputs/expected/test_results.md) |
| 17-K3-taint-effects | 4 | PASS | [test_results.md](../../exercises/17-K3-taint-effects/outputs/expected/test_results.md) |
| 17-K4-mig-strategies | 4 | PASS | [test_results.md](../../exercises/17-K4-mig-strategies/outputs/expected/test_results.md) |
| 17-K5-squeue-reasons | 4 | PASS | [test_results.md](../../exercises/17-K5-squeue-reasons/outputs/expected/test_results.md) |
| 17-K6-topology-manager-loop | 4 | PASS | [test_results.md](../../exercises/17-K6-topology-manager-loop/outputs/expected/test_results.md) |
| 17-K7-fair-share-factor | 4 | PASS | [test_results.md](../../exercises/17-K7-fair-share-factor/outputs/expected/test_results.md) |
| 17-L1-orion-scheduler-lab | 4 | PASS | [test_results.md](../../exercises/17-L1-orion-scheduler-lab/outputs/expected/test_results.md) |
| 17-M1-kubernetes-vs-slurm | 4 | PASS | [test_results.md](../../exercises/17-M1-kubernetes-vs-slurm/outputs/expected/test_results.md) |
| 17-M2-scheduling-policy-design | 4 | PASS | [test_results.md](../../exercises/17-M2-scheduling-policy-design/outputs/expected/test_results.md) |
| 17-M3-pending-troubleshooting-guide | 4 | PASS | [test_results.md](../../exercises/17-M3-pending-troubleshooting-guide/outputs/expected/test_results.md) |
| 17-R1-single-pass-simulator | 4 | PASS | [test_results.md](../../exercises/17-R1-single-pass-simulator/outputs/expected/test_results.md) |
| 17-R2-decayed-fair-share | 4 | PASS | [test_results.md](../../exercises/17-R2-decayed-fair-share/outputs/expected/test_results.md) |
| 17-R3-correlated-rack-events | 4 | PASS | [test_results.md](../../exercises/17-R3-correlated-rack-events/outputs/expected/test_results.md) |
| 17-R4-measuring-gang-wait | 4 | PASS | [test_results.md](../../exercises/17-R4-measuring-gang-wait/outputs/expected/test_results.md) |
| 17-T1-inference-pool-pending | 4 | PASS | [test_results.md](../../exercises/17-T1-inference-pool-pending/outputs/expected/test_results.md) |
| 17-W1-gang-feasibility-cost | 4 | PASS | [test_results.md](../../exercises/17-W1-gang-feasibility-cost/outputs/expected/test_results.md) |
| 17-W2-priority-vs-fair-share | 4 | PASS | [test_results.md](../../exercises/17-W2-priority-vs-fair-share/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
