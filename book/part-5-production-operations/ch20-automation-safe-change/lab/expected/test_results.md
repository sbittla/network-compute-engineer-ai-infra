# Test results: ch20

**PASS**: 90 passed, 0 skipped, 90 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.504 |
| `test_lab_starter_fails_gracefully` | PASS | 0.444 |
| `test_lab_runs_without_generator` | PASS | 0.695 |
| `test_lab_golden_solution_report` | PASS | 0.001 |
| `test_lab_golden_starter_report` | PASS | 0.373 |
| `test_exercise_index` | PASS | 0.029 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 20-D1-drift-policy-break-glass | 4 | PASS | [test_results.md](../../exercises/20-D1-drift-policy-break-glass/outputs/expected/test_results.md) |
| 20-DEL-automation-sample-runbook | 4 | PASS | [test_results.md](../../exercises/20-DEL-automation-sample-runbook/outputs/expected/test_results.md) |
| 20-K1-idempotency | 4 | PASS | [test_results.md](../../exercises/20-K1-idempotency/outputs/expected/test_results.md) |
| 20-K2-level-vs-edge-triggered | 4 | PASS | [test_results.md](../../exercises/20-K2-level-vs-edge-triggered/outputs/expected/test_results.md) |
| 20-K3-state-plan-drift | 4 | PASS | [test_results.md](../../exercises/20-K3-state-plan-drift/outputs/expected/test_results.md) |
| 20-K4-validation-layers | 4 | PASS | [test_results.md](../../exercises/20-K4-validation-layers/outputs/expected/test_results.md) |
| 20-K5-gitops-break-glass | 4 | PASS | [test_results.md](../../exercises/20-K5-gitops-break-glass/outputs/expected/test_results.md) |
| 20-K6-proceed-hold-abort | 4 | PASS | [test_results.md](../../exercises/20-K6-proceed-hold-abort/outputs/expected/test_results.md) |
| 20-K7-own-baseline-median | 4 | PASS | [test_results.md](../../exercises/20-K7-own-baseline-median/outputs/expected/test_results.md) |
| 20-K8-safety-controls | 4 | PASS | [test_results.md](../../exercises/20-K8-safety-controls/outputs/expected/test_results.md) |
| 20-L1-safe-change-lab | 4 | PASS | [test_results.md](../../exercises/20-L1-safe-change-lab/outputs/expected/test_results.md) |
| 20-M1-idempotent-config-validator | 4 | PASS | [test_results.md](../../exercises/20-M1-idempotent-config-validator/outputs/expected/test_results.md) |
| 20-M2-leaf-qos-canary-design | 4 | PASS | [test_results.md](../../exercises/20-M2-leaf-qos-canary-design/outputs/expected/test_results.md) |
| 20-M3-unsafe-plan-review | 4 | PASS | [test_results.md](../../exercises/20-M3-unsafe-plan-review/outputs/expected/test_results.md) |
| 20-R1-big-bang-conditions | 4 | PASS | [test_results.md](../../exercises/20-R1-big-bang-conditions/outputs/expected/test_results.md) |
| 20-R2-real-telemetry-traps | 4 | PASS | [test_results.md](../../exercises/20-R2-real-telemetry-traps/outputs/expected/test_results.md) |
| 20-R3-keyword-checker-limits | 4 | PASS | [test_results.md](../../exercises/20-R3-keyword-checker-limits/outputs/expected/test_results.md) |
| 20-R4-rdma-mtu-evidence-gap | 4 | PASS | [test_results.md](../../exercises/20-R4-rdma-mtu-evidence-gap/outputs/expected/test_results.md) |
| 20-T1-plan-that-removed-pfc | 4 | PASS | [test_results.md](../../exercises/20-T1-plan-that-removed-pfc/outputs/expected/test_results.md) |
| 20-W1-ipv6-vlan-mtu-budget | 4 | PASS | [test_results.md](../../exercises/20-W1-ipv6-vlan-mtu-budget/outputs/expected/test_results.md) |
| 20-W2-orion-xl-wave-plan | 4 | PASS | [test_results.md](../../exercises/20-W2-orion-xl-wave-plan/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
