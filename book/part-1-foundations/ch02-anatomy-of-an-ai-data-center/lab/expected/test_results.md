# Test results: ch02

**PASS**: 94 passed, 0 skipped, 94 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.368 |
| `test_lab_starter_fails_gracefully` | PASS | 0.284 |
| `test_lab_runs_without_generator` | PASS | 0.694 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 0.252 |
| `test_exercise_index` | PASS | 0.032 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| 2.1.1-power-limited-rack | 4 | PASS | [test_results.md](../../exercises/2.1.1-power-limited-rack/outputs/expected/test_results.md) |
| 2.1.2-three-networks | 4 | PASS | [test_results.md](../../exercises/2.1.2-three-networks/outputs/expected/test_results.md) |
| 2.1.3-2n-rack-capacity | 4 | PASS | [test_results.md](../../exercises/2.1.3-2n-rack-capacity/outputs/expected/test_results.md) |
| 2.1.4-tdp-versus-peak | 4 | PASS | [test_results.md](../../exercises/2.1.4-tdp-versus-peak/outputs/expected/test_results.md) |
| 2.1.5-fws-tcs-approach | 4 | PASS | [test_results.md](../../exercises/2.1.5-fws-tcs-approach/outputs/expected/test_results.md) |
| 2.1.6-sw-power-cap | 4 | PASS | [test_results.md](../../exercises/2.1.6-sw-power-cap/outputs/expected/test_results.md) |
| 2.1.7-allocation-mfu-goodput | 4 | PASS | [test_results.md](../../exercises/2.1.7-allocation-mfu-goodput/outputs/expected/test_results.md) |
| 2.1.8-optics-count | 4 | PASS | [test_results.md](../../exercises/2.1.8-optics-count/outputs/expected/test_results.md) |
| 2.10-grow-orion-512 | 4 | PASS | [test_results.md](../../exercises/2.10-grow-orion-512/outputs/expected/test_results.md) |
| 2.11.1-least-confident-number | 4 | PASS | [test_results.md](../../exercises/2.11.1-least-confident-number/outputs/expected/test_results.md) |
| 2.11.2-rail-leaf-spof-risk | 4 | PASS | [test_results.md](../../exercises/2.11.2-rail-leaf-spof-risk/outputs/expected/test_results.md) |
| 2.11.3-lab-blind-spots | 4 | PASS | [test_results.md](../../exercises/2.11.3-lab-blind-spots/outputs/expected/test_results.md) |
| 2.11.4-pue-is-not-enough | 4 | PASS | [test_results.md](../../exercises/2.11.4-pue-is-not-enough/outputs/expected/test_results.md) |
| 2.11.5-ownership-gap | 4 | PASS | [test_results.md](../../exercises/2.11.5-ownership-gap/outputs/expected/test_results.md) |
| 2.2-small-cluster-bom | 4 | PASS | [test_results.md](../../exercises/2.2-small-cluster-bom/outputs/expected/test_results.md) |
| 2.3-capacity-model | 4 | PASS | [test_results.md](../../exercises/2.3-capacity-model/outputs/expected/test_results.md) |
| 2.4-orion-capacity-lab | 4 | PASS | [test_results.md](../../exercises/2.4-orion-capacity-lab/outputs/expected/test_results.md) |
| 2.5-vega-spofs | 4 | PASS | [test_results.md](../../exercises/2.5-vega-spofs/outputs/expected/test_results.md) |
| 2.6-dlc-rack-density | 4 | PASS | [test_results.md](../../exercises/2.6-dlc-rack-density/outputs/expected/test_results.md) |
| 2.7-maintenance-window-slowdown | 4 | PASS | [test_results.md](../../exercises/2.7-maintenance-window-slowdown/outputs/expected/test_results.md) |
| 2.8-power-cap-sweep | 4 | PASS | [test_results.md](../../exercises/2.8-power-cap-sweep/outputs/expected/test_results.md) |
| 2.9-rack-x-power-thermal | 4 | PASS | [test_results.md](../../exercises/2.9-rack-x-power-thermal/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
