"""Package test suite. Runs inside the package's container, after the image is built.

    python -m pytest /opt/harness/test_package.py --pkg /work/pkg

Lab contract (docs/LAB_STANDARDS.md section 4) plus golden outputs and the exercise folders.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from common import (EXERCISE_KINDS, EXERCISE_TYPES, META_REQUIRED, Exercise, Package,
                    dump_json, lab_checks_payload, marking_payload, normalize, prompt_block, run_checker,
                    run_solver, squash)


@pytest.fixture(scope="session")
def pkg(pytestconfig: pytest.Config) -> Package:
    return Package(Path(pytestconfig.getoption("--pkg")))


@pytest.fixture(scope="session")
def solution_report(pkg: Package) -> tuple[int, str]:
    return run_checker(pkg.checker, "solution")


# --- lab ----------------------------------------------------------------------------------------

def test_lab_solution_passes(solution_report: tuple[int, str]) -> None:
    rc, out = solution_report
    assert rc == 0, out


def test_lab_starter_fails_gracefully(pkg: Package) -> None:
    rc, out = run_checker(pkg.checker, "starter")
    assert rc != 0, "starter must not pass while TODOs remain"
    assert "Traceback (most recent call last)" not in out, out


def test_lab_runs_without_generator(pkg: Package, tmp_path: Path) -> None:
    """Student release has no tools/: regeneration checks must SKIP, not FAIL."""
    copy = tmp_path / pkg.root.name
    shutil.copytree(pkg.root, copy, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.rmtree(Package(copy).lab_dir / "tools", ignore_errors=True)
    rc, out = run_checker(Package(copy).checker, "solution")
    assert rc == 0, out


def test_lab_golden_solution_report(pkg: Package, solution_report: tuple[int, str]) -> None:
    golden = pkg.golden_dir / "check_solution.txt"
    assert golden.is_file(), f"missing {golden}; run: python scripts/docker_labs.py outputs"
    assert normalize(solution_report[1]) == normalize(golden.read_text(encoding="utf-8"))


def test_lab_golden_starter_report(pkg: Package) -> None:
    golden = pkg.golden_dir / "check_starter.txt"
    assert golden.is_file(), f"missing {golden}; run: python scripts/docker_labs.py outputs"
    assert normalize(run_checker(pkg.checker, "starter")[1]) == normalize(golden.read_text(encoding="utf-8"))


# --- exercise folders ---------------------------------------------------------------------------

def test_exercise_index(pkg: Package) -> None:
    if pkg.is_capstone:
        pytest.skip("capstones use deliverable templates, not exercise folders")
    index = pkg.exercises_dir / "README.md"
    assert index.is_file(), "exercises/README.md (index) missing"
    text = index.read_text(encoding="utf-8")
    learner = sorted(p.name for p in pkg.exercises_dir.iterdir() if p.is_dir())
    solved = sorted(e.name for e in pkg.exercises())
    assert learner == solved, f"learner folders and solution folders differ: {set(learner) ^ set(solved)}"
    assert solved, "no exercise folders"
    for name in solved:
        assert f"]({name}/" in text or f"]({name})" in text, f"index does not link {name}"
    m = re.search(r"Exercise count:\s*(\d+)", text)
    assert m and int(m.group(1)) == len(solved), "index 'Exercise count: N' must equal the folder count"


def test_exercise_meta(exercise: Exercise) -> None:
    m = exercise.meta
    missing = [k for k in META_REQUIRED if k not in m]
    assert not missing, f"meta.yaml missing {missing}"
    assert m["folder"] == exercise.name
    assert m["kind"] in EXERCISE_KINDS
    assert m["type"] in EXERCISE_TYPES
    assert m["difficulty"] in (1, 2, 3)
    assert m["tier"] in ("L1", "L2", "L3")
    assert sum(int(c["points"]) for c in m["marking"]) == int(m["points"]), "marking points must sum to points"
    assert all(str(c.get("criterion", "")).strip() for c in m["marking"])
    if m["kind"] == "lab":
        assert m.get("lab_checks"), "kind: lab needs lab_checks"


def test_exercise_prompt_matches_source(pkg: Package, exercise: Exercise) -> None:
    readme = exercise.learner_dir / "README.md"
    assert readme.is_file(), f"missing learner {readme}"
    block = prompt_block(readme.read_text(encoding="utf-8"))
    assert block and block.strip(), "README needs the prompt between <!-- prompt:start --> and <!-- prompt:end -->"
    source = squash((pkg.root / "exercises.md").read_text(encoding="utf-8"))
    assert squash(block) in source, "prompt text has drifted from exercises.md"


def test_exercise_solution_present(exercise: Exercise) -> None:
    answer = exercise.sol_dir / "solution" / "answer.md"
    assert answer.is_file() and len(answer.read_text(encoding="utf-8").split()) >= 40, "solution/answer.md too short"
    if exercise.meta["kind"] == "computed":
        assert exercise.solve_script.is_file(), "kind: computed needs solution/solve.py"


def test_exercise_outputs_regenerate(exercise: Exercise, solution_report: tuple[int, str], tmp_path: Path) -> None:
    committed = exercise.outputs_dir
    assert committed.is_dir(), "outputs/ missing; run: python scripts/docker_labs.py outputs"
    fresh = tmp_path / "outputs"
    fresh.mkdir()
    if exercise.meta["kind"] == "computed":
        rc, log = run_solver(exercise, fresh)
        assert rc == 0, f"solve.py failed (its assertions encode the answer key):\n{log}"
        produced = [p for p in fresh.rglob("*") if p.is_file()]
        assert produced, "solve.py wrote no outputs"
    if exercise.meta["kind"] == "lab":
        payload = lab_checks_payload(exercise, normalize(solution_report[1]))
        missing = [k for k, v in payload["lab_checks"].items() if not v or not v.startswith("PASS")]
        assert not missing, f"lab checks not passing in the solution report: {missing}"
        (fresh / "lab_checks.json").write_text(dump_json(payload), encoding="utf-8")
    (fresh / "marking.json").write_text(dump_json(marking_payload(exercise)), encoding="utf-8")

    names = sorted(str(p.relative_to(fresh)) for p in fresh.rglob("*") if p.is_file())
    have = sorted(str(p.relative_to(committed)) for p in committed.rglob("*") if p.is_file())
    assert names == have, f"output file set differs: {set(names) ^ set(have)}"
    for rel in names:
        a = (fresh / rel).read_text(encoding="utf-8")
        b = (committed / rel).read_text(encoding="utf-8")
        assert normalize(a) == normalize(b), f"{rel} differs from committed output"
