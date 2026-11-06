# Test results: capstone-f

**PASS**: 5 passed, 5 skipped, 10 tests.

## Lab and package tests

| Test | Result | Time (s) |
|---|---|---|
| `test_lab_solution_passes` | PASS | 12.156 |
| `test_lab_starter_fails_gracefully` | PASS | 1.520 |
| `test_lab_runs_without_generator` | PASS | 10.562 |
| `test_lab_golden_solution_report` | PASS | 0.005 |
| `test_lab_golden_starter_report` | PASS | 1.594 |
| `test_exercise_index` | SKIP | 0.002 | capstones use deliverable templates, not exercise folders

## Exercise tests

| Exercise | Tests | Result | Details |
|---|---|---|---|
| NOTSET | 4 | PASS | [test_results.md](../../exercises/NOTSET/outputs/expected/test_results.md) |

Skipped tests are the exercise-folder tests, which capstones do not have.

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `2a97c55` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
