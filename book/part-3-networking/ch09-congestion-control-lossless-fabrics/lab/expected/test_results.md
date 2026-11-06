# Test results: ch09

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 1.840 |
| `test_lab_starter_fails_gracefully` | PASS | 1.054 |
| `test_lab_runs_without_generator` | PASS | 3.686 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 1.059 |
| `test_exercise_index` | PASS | 0.035 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| D1-second-lossless-class | 4 | PASS | [test_results.md](../../exercises/D1-second-lossless-class/outputs/expected/test_results.md) |
| H1-congestion-telemetry-lab | 4 | PASS | [test_results.md](../../exercises/H1-congestion-telemetry-lab/outputs/expected/test_results.md) |
| K1-roles | 4 | PASS | [test_results.md](../../exercises/K1-roles/outputs/expected/test_results.md) |
| K2-pause-arithmetic | 4 | PASS | [test_results.md](../../exercises/K2-pause-arithmetic/outputs/expected/test_results.md) |
| K3-ecn-codepoints | 4 | PASS | [test_results.md](../../exercises/K3-ecn-codepoints/outputs/expected/test_results.md) |
| K4-cnp-class | 4 | PASS | [test_results.md](../../exercises/K4-cnp-class/outputs/expected/test_results.md) |
| K5-xoff-headroom | 4 | PASS | [test_results.md](../../exercises/K5-xoff-headroom/outputs/expected/test_results.md) |
| K6-pause-direction | 4 | PASS | [test_results.md](../../exercises/K6-pause-direction/outputs/expected/test_results.md) |
| K7-watermarks | 4 | PASS | [test_results.md](../../exercises/K7-watermarks/outputs/expected/test_results.md) |
| K8-storm-or-incast | 4 | PASS | [test_results.md](../../exercises/K8-storm-or-incast/outputs/expected/test_results.md) |
| O1-synthetic-time-series | 4 | PASS | [test_results.md](../../exercises/O1-synthetic-time-series/outputs/expected/test_results.md) |
| O2-why-not-pfc-everywhere | 4 | PASS | [test_results.md](../../exercises/O2-why-not-pfc-everywhere/outputs/expected/test_results.md) |
| O3-controlled-experiment | 4 | PASS | [test_results.md](../../exercises/O3-controlled-experiment/outputs/expected/test_results.md) |
| R1-trust-model-numbers | 4 | PASS | [test_results.md](../../exercises/R1-trust-model-numbers/outputs/expected/test_results.md) |
| R2-sampling-blind-spots | 4 | PASS | [test_results.md](../../exercises/R2-sampling-blind-spots/outputs/expected/test_results.md) |
| R3-proof-vs-correlation | 4 | PASS | [test_results.md](../../exercises/R3-proof-vs-correlation/outputs/expected/test_results.md) |
| R4-root-finder-limits | 4 | PASS | [test_results.md](../../exercises/R4-root-finder-limits/outputs/expected/test_results.md) |
| T1-lossless-discards-uplink | 4 | PASS | [test_results.md](../../exercises/T1-lossless-discards-uplink/outputs/expected/test_results.md) |
| W1-headroom-budget | 4 | PASS | [test_results.md](../../exercises/W1-headroom-budget/outputs/expected/test_results.md) |
| W2-incast-feedback | 4 | PASS | [test_results.md](../../exercises/W2-incast-feedback/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
