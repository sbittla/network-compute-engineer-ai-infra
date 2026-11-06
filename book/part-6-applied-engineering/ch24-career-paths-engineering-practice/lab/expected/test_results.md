# Test results: ch24

**PASS**: 86 passed, 0 skipped, 86 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 0.514 |
| `test_lab_starter_fails_gracefully` | PASS | 0.470 |
| `test_lab_runs_without_generator` | PASS | 1.137 |
| `test_lab_golden_solution_report` | PASS | 0.002 |
| `test_lab_golden_starter_report` | PASS | 0.485 |
| `test_exercise_index` | PASS | 0.071 |

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| D1-twelve-week-plan | 4 | PASS | [test_results.md](../../exercises/D1-twelve-week-plan/outputs/expected/test_results.md) |
| K1-roles-paged-for | 4 | PASS | [test_results.md](../../exercises/K1-roles-paged-for/outputs/expected/test_results.md) |
| K2-evidence-caps | 4 | PASS | [test_results.md](../../exercises/K2-evidence-caps/outputs/expected/test_results.md) |
| K3-senior-versus-staff | 4 | PASS | [test_results.md](../../exercises/K3-senior-versus-staff/outputs/expected/test_results.md) |
| K4-job-posting-register | 4 | PASS | [test_results.md](../../exercises/K4-job-posting-register/outputs/expected/test_results.md) |
| K5-tp-inside-node | 4 | PASS | [test_results.md](../../exercises/K5-tp-inside-node/outputs/expected/test_results.md) |
| K6-where-bytes-go | 4 | PASS | [test_results.md](../../exercises/K6-where-bytes-go/outputs/expected/test_results.md) |
| K7-discriminating-tests | 4 | PASS | [test_results.md](../../exercises/K7-discriminating-tests/outputs/expected/test_results.md) |
| K8-representative-not-current | 4 | PASS | [test_results.md](../../exercises/K8-representative-not-current/outputs/expected/test_results.md) |
| L1-readiness-register-lab | 4 | PASS | [test_results.md](../../exercises/L1-readiness-register-lab/outputs/expected/test_results.md) |
| M1-target-role-skills-map | 4 | PASS | [test_results.md](../../exercises/M1-target-role-skills-map/outputs/expected/test_results.md) |
| M2-system-design-presentation | 4 | PASS | [test_results.md](../../exercises/M2-system-design-presentation/outputs/expected/test_results.md) |
| M3-case-study | 4 | PASS | [test_results.md](../../exercises/M3-case-study/outputs/expected/test_results.md) |
| R1-readiness-score-bias | 4 | PASS | [test_results.md](../../exercises/R1-readiness-score-bias/outputs/expected/test_results.md) |
| R2-competency-weighting | 4 | PASS | [test_results.md](../../exercises/R2-competency-weighting/outputs/expected/test_results.md) |
| R3-skill-versus-reasoning | 4 | PASS | [test_results.md](../../exercises/R3-skill-versus-reasoning/outputs/expected/test_results.md) |
| R4-python-bottleneck-evidence | 4 | PASS | [test_results.md](../../exercises/R4-python-bottleneck-evidence/outputs/expected/test_results.md) |
| T1-interview-thermal-straggler | 4 | PASS | [test_results.md](../../exercises/T1-interview-thermal-straggler/outputs/expected/test_results.md) |
| WP1-readiness-second-role | 4 | PASS | [test_results.md](../../exercises/WP1-readiness-second-role/outputs/expected/test_results.md) |
| WP2-512-gpu-variant | 4 | PASS | [test_results.md](../../exercises/WP2-512-gpu-variant/outputs/expected/test_results.md) |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
