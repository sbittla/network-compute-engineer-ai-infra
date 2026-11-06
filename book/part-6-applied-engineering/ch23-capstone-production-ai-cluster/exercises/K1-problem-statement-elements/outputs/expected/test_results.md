# Test results: K1 Five elements of a capstone problem statement

**PASS**: 4/4 tests passed. These tests check that the prompt here matches `exercises.md`, that a worked solution and marking scheme exist, and that the reference results in this folder regenerate exactly.

| Test | Result | Time (s) |
|---|---|---|
| `test_exercise_meta` | PASS | 0.001 |
| `test_exercise_prompt_matches_source` | PASS | 0.002 |
| `test_exercise_solution_present` | PASS | 0.001 |
| `test_exercise_outputs_regenerate` | PASS | 0.008 |

Run locally with `python -m pytest docker/harness/test_package.py --pkg <package>`; the lab containers (`python scripts/docker_labs.py test <id>`) run the same suite.

Generated 2026-11-05 from commit `025bde5` with Python 3.13.14 by `scripts/make_expected_outputs.py`.
