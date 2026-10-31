"""Regenerate a package's committed outputs inside its container (package bind-mounted read-write).

    python /opt/harness/generate_outputs.py /work/pkg

Writes:
  * lab checker reports      -> solutions/lab/outputs/ (chapters) or instructor/outputs/ (capstones)
  * per-exercise outputs     -> solutions/exercises/<folder>/outputs/
      - result files from solution/solve.py   (kind: computed)
      - lab_checks.json from the solution report (kind: lab)
      - marking.json from meta.yaml            (every exercise)
test_package.py then requires the committed files to equal a fresh regeneration.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from common import Package, dump_json, lab_checks_payload, marking_payload, normalize, run_checker, run_solver


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main(root: str) -> int:
    pkg = Package(Path(root))
    failures = 0

    rc_sol, sol = run_checker(pkg.checker, "solution")
    rc_sta, sta = run_checker(pkg.checker, "starter")
    write(pkg.golden_dir / "check_solution.txt", normalize(sol))
    write(pkg.golden_dir / "check_starter.txt", normalize(sta))
    print(f"lab: solution rc={rc_sol}  starter rc={rc_sta}  -> {pkg.golden_dir.relative_to(pkg.root)}")
    if rc_sol != 0:
        failures += 1

    for ex in pkg.exercises():
        out = ex.outputs_dir
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        status = "ok"
        if ex.meta.get("kind") == "computed":
            rc, log = run_solver(ex, out)
            if rc != 0:
                failures += 1
                status = f"SOLVER FAILED rc={rc}\n{log}"
            for f in out.rglob("*"):
                if f.is_file() and f.suffix in {".json", ".md", ".txt", ".csv", ".yaml"}:
                    f.write_text(normalize(f.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        if ex.meta.get("kind") == "lab":
            write(out / "lab_checks.json", dump_json(lab_checks_payload(ex, normalize(sol))))
        write(out / "marking.json", dump_json(marking_payload(ex)))
        print(f"exercise {ex.name}: {status}")
    print(f"{'OK' if failures == 0 else 'FAILED'}: {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/work/pkg"))
