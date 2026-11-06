# Test results: ch08

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 1.853 |
| `test_lab_starter_fails_gracefully` | PASS | 1.190 |
| `test_lab_runs_without_generator` | PASS | 2.547 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 1.110 |
| `test_exercise_index` | PASS | 0.074 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 8.1-keys-access-rights | 4 | PASS | [test_results.md](../../exercises/8.1-keys-access-rights/outputs/expected/test_results.md) |
| 8.10-two-data-paths | 4 | PASS | [test_results.md](../../exercises/8.10-two-data-paths/outputs/expected/test_results.md) |
| 8.11-rocev2-vs-ib-design-note | 4 | PASS | [test_results.md](../../exercises/8.11-rocev2-vs-ib-design-note/outputs/expected/test_results.md) |
| 8.12-readiness-checklist | 4 | PASS | [test_results.md](../../exercises/8.12-readiness-checklist/outputs/expected/test_results.md) |
| 8.13-readiness-validator-lab | 4 | PASS | [test_results.md](../../exercises/8.13-readiness-validator-lab/outputs/expected/test_results.md) |
| 8.14-l3-measure-a-rail | 4 | PASS | [test_results.md](../../exercises/8.14-l3-measure-a-rail/outputs/expected/test_results.md) |
| 8.15-small-messages-mtu | 4 | PASS | [test_results.md](../../exercises/8.15-small-messages-mtu/outputs/expected/test_results.md) |
| 8.16-orion-xl-fabric-policy | 4 | PASS | [test_results.md](../../exercises/8.16-orion-xl-fabric-policy/outputs/expected/test_results.md) |
| 8.17-two-node-bw-gaps | 4 | PASS | [test_results.md](../../exercises/8.17-two-node-bw-gaps/outputs/expected/test_results.md) |
| 8.18-ready-false-negatives | 4 | PASS | [test_results.md](../../exercises/8.18-ready-false-negatives/outputs/expected/test_results.md) |
| 8.19-simulated-vs-measured | 4 | PASS | [test_results.md](../../exercises/8.19-simulated-vs-measured/outputs/expected/test_results.md) |
| 8.2-silent-arrival | 4 | PASS | [test_results.md](../../exercises/8.2-silent-arrival/outputs/expected/test_results.md) |
| 8.20-correlation-vs-causation | 4 | PASS | [test_results.md](../../exercises/8.20-correlation-vs-causation/outputs/expected/test_results.md) |
| 8.3-qp-state-parameters | 4 | PASS | [test_results.md](../../exercises/8.3-qp-state-parameters/outputs/expected/test_results.md) |
| 8.4-rocev1-vs-v2 | 4 | PASS | [test_results.md](../../exercises/8.4-rocev1-vs-v2/outputs/expected/test_results.md) |
| 8.5-udp-source-port-entropy | 4 | PASS | [test_results.md](../../exercises/8.5-udp-source-port-entropy/outputs/expected/test_results.md) |
| 8.6-reading-ibstat | 4 | PASS | [test_results.md](../../exercises/8.6-reading-ibstat/outputs/expected/test_results.md) |
| 8.7-lossless-two-ways | 4 | PASS | [test_results.md](../../exercises/8.7-lossless-two-ways/outputs/expected/test_results.md) |
| 8.8-wire-efficiency-marking | 4 | PASS | [test_results.md](../../exercises/8.8-wire-efficiency-marking/outputs/expected/test_results.md) |
| 8.9-price-of-lost-packet | 4 | PASS | [test_results.md](../../exercises/8.9-price-of-lost-packet/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
