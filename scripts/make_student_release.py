#!/usr/bin/env python3
"""Copy the repository to a learner-facing release with instructor material removed.

Removes every chapter ``solutions/`` and ``review/`` folder, every capstone ``instructor/`` folder, and the
dataset generators (``lab/tools/`` and ``starter-kit/tools/``), because generators encode the planted faults.
Learners use the committed ``data/``; checker regeneration checks skip when the generator is absent.

Learner-visible reference results (``exercises/*/outputs/expected/``, ``lab/expected/`` and
``starter-kit/expected/``, written by ``scripts/make_expected_outputs.py``) are kept by default so
self-study learners can check their work. For a graded cohort, pass ``--without-expected``.

Usage:
    python scripts/make_student_release.py ../ai-infra-student-edition
    python scripts/make_student_release.py ../ai-infra-graded-cohort --without-expected
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_DIRS = {"solutions", "review", "instructor", ".git", "__pycache__", ".pytest_cache"}
EXCLUDE_FILES = {"AI_Infrastructure_Engineering_Definitive_Outline_v2_Enhanced.docx"}


GENERATOR_PARENTS = {"lab", "starter-kit"}


EXPECTED_PARENTS = {"outputs", "lab", "starter-kit"}
WITHOUT_EXPECTED = False


def ignore(directory: str, names: list[str]) -> set[str]:
    skipped = {n for n in names if n in EXCLUDE_DIRS or n in EXCLUDE_FILES}
    if Path(directory).name in GENERATOR_PARENTS and "tools" in names:
        skipped.add("tools")
    if WITHOUT_EXPECTED and Path(directory).name in EXPECTED_PARENTS and "expected" in names:
        skipped.add("expected")
    return skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dest", type=Path, help="destination directory (must not exist)")
    parser.add_argument("--without-expected", action="store_true",
                        help="also remove the learner-visible reference results (outputs/expected/, lab/expected/)")
    args = parser.parse_args()
    global WITHOUT_EXPECTED
    WITHOUT_EXPECTED = args.without_expected
    dest = args.dest.resolve()
    if dest.exists():
        print(f"error: {dest} already exists", file=sys.stderr)
        return 1
    if ROOT in dest.parents or dest == ROOT:
        print("error: destination must be outside the repository", file=sys.stderr)
        return 1
    shutil.copytree(ROOT, dest, ignore=ignore)
    print(f"Student release written to {dest}")
    print("Note: lab checkers still work with --impl starter; --impl solution is unavailable by design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
