#!/usr/bin/env python3
"""Copy the repository to a learner-facing release with instructor material removed.

Removes every chapter ``solutions/`` and ``review/`` folder, every capstone ``instructor/`` folder, and the
dataset generators (``lab/tools/`` and ``starter-kit/tools/``), because generators encode the planted faults.
Learners use the committed ``data/``; checker regeneration checks skip when the generator is absent.

Usage:
    python scripts/make_student_release.py ../ai-infra-student-edition
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


def ignore(directory: str, names: list[str]) -> set[str]:
    skipped = {n for n in names if n in EXCLUDE_DIRS or n in EXCLUDE_FILES}
    if Path(directory).name in GENERATOR_PARENTS and "tools" in names:
        skipped.add("tools")
    return skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dest", type=Path, help="destination directory (must not exist)")
    args = parser.parse_args()
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
