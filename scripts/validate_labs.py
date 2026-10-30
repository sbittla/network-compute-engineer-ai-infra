#!/usr/bin/env python3
"""Validate every lab in the book against the check.py contract.

For each ``lab/check.py`` (chapters) and ``check.py`` under ``capstones/*/starter-kit``:
  * ``--impl solution`` must exit 0
  * ``--impl starter`` must exit non-zero without a Python traceback
  * release check: with the dataset generator removed (as in the student release, see
    scripts/make_student_release.py), ``--impl solution`` must still exit 0 -- regeneration
    checks have to SKIP, not FAIL, when ``tools/`` is absent

Usage:
    python scripts/validate_labs.py            # all labs
    python scripts/validate_labs.py ch07 ch08  # only labs whose path contains these substrings
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_S = 120


def find_checkers(filters: list[str]) -> list[Path]:
    checkers = sorted(ROOT.glob("book/*/*/lab/check.py")) + sorted(ROOT.glob("capstones/*/starter-kit/check.py"))
    if filters:
        checkers = [c for c in checkers if any(f in str(c) for f in filters)]
    return checkers


def run(checker: Path, impl: str) -> tuple[int, str, float]:
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(checker), "--impl", impl],
        cwd=checker.parent,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout + proc.stderr, time.perf_counter() - t0


def run_without_generator(checker: Path) -> tuple[int, str]:
    """Run ``--impl solution`` on a copy of the package whose ``tools/`` generator dir is removed."""
    package = checker.parent.parent  # chapter dir or capstone dir
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / package.name
        shutil.copytree(package, copy, ignore=shutil.ignore_patterns("__pycache__"))
        tools = copy / checker.parent.name / "tools"
        if tools.exists():
            shutil.rmtree(tools)
        rc, out, _ = run(copy / checker.parent.name / checker.name, "solution")
    return rc, out


def generator_mentions(checker: Path) -> list[str]:
    """Learner-facing lines that reference the generator without marking it instructor-only."""
    package = checker.parent.parent
    hits = []
    for doc in (package / "README.md", checker.parent / "README.md"):
        if not doc.exists():
            continue
        lines = doc.read_text(encoding="utf-8").splitlines()
        for n, line in enumerate(lines, 1):
            if "tools/" not in line or "generat" not in line.lower():
                continue
            # Prose may wrap: accept the marking anywhere in the same paragraph (table rows stand alone).
            para = [line]
            if not line.lstrip().startswith("|"):
                for nxt in lines[n:n + 3]:
                    if not nxt.strip() or nxt.lstrip().startswith(("|", "#", "```")):
                        break
                    para.append(nxt)
            if "instructor" not in " ".join(para).lower():
                hits.append(f"{doc.relative_to(ROOT)}:{n}: {line.strip()[:100]}")
    return hits


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("filters", nargs="*", help="substring filters on checker path")
    parser.add_argument("-v", "--verbose", action="store_true", help="print checker output")
    args = parser.parse_args()

    checkers = find_checkers(args.filters)
    if not checkers:
        print("No checkers found.")
        return 1

    failures = 0
    for checker in checkers:
        rel = checker.relative_to(ROOT)
        sol_rc, sol_out, sol_t = run(checker, "solution")
        st_rc, st_out, st_t = run(checker, "starter")
        rel_rc, rel_out = run_without_generator(checker)
        sol_ok = sol_rc == 0
        st_ok = st_rc != 0 and "Traceback" not in st_out
        rel_ok = rel_rc == 0 and "Traceback" not in rel_out
        gen_hits = generator_mentions(checker)
        status = "OK  " if sol_ok and st_ok and rel_ok and not gen_hits else "FAIL"
        failures += status == "FAIL"
        print(f"{status} {rel}  solution={'pass' if sol_ok else 'FAIL'} ({sol_t:.1f}s)  "
              f"starter={'fails-gracefully' if st_ok else 'BAD'} ({st_t:.1f}s)  "
              f"no-generator={'pass' if rel_ok else 'FAIL'}  "
              f"docs={'ok' if not gen_hits else 'GENERATOR-NOT-MARKED'}")
        for hit in gen_hits:
            print(f"  learner doc mentions generator without 'instructor': {hit}")
        if args.verbose or not sol_ok:
            print("  --- solution output ---\n  " + sol_out.strip().replace("\n", "\n  "))
        if args.verbose or not st_ok:
            print("  --- starter output ---\n  " + st_out.strip().replace("\n", "\n  "))

    print(f"\n{len(checkers) - failures}/{len(checkers)} labs valid")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
