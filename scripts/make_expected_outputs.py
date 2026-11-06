#!/usr/bin/env python3
"""Write learner-visible expected outputs next to every exercise, lab and capstone starter kit.

For each chapter exercise it creates ``exercises/<ID>-<slug>/outputs/expected/`` and for each lab and
capstone starter kit ``lab/expected/`` (``starter-kit/expected/``), by RUNNING the reference material now:

- computed exercises: the reference ``solve.py --out`` writes ``result.md`` / ``result.json``;
- lab exercises: the lab checker runs with ``--impl solution`` and the exercise's named checks are extracted;
- every exercise: the worked answer (``answer.md``) and the marking scheme (``marking.md``);
- every lab / starter kit: the checker's output for the reference solution and for the untouched starter.

Every fresh result is compared with the golden outputs the test harness already verifies
(``solutions/.../outputs`` and ``instructor/outputs``); the script refuses to write anything that differs.
Each ``expected/`` folder gets a README stamped with the run date, commit and Python version.

    python scripts/make_expected_outputs.py            # all packages
    python scripts/make_expected_outputs.py ch09 capstone-b

The student release can leave these out: ``python scripts/make_student_release.py DEST --without-expected``.
"""
from __future__ import annotations

import datetime as dt
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docker" / "harness"))
from common import (Package, dump_json, lab_checks_payload, marking_payload, normalize,  # noqa: E402
                    run_checker, run_solver)

TODAY = dt.date.today().isoformat()
COMMIT = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                        text=True).stdout.strip() or "unknown"
PY = platform.python_version()
STAMP = f"Generated {TODAY} from commit `{COMMIT}` with Python {PY} by `scripts/make_expected_outputs.py`."


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def fresh_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def same(a: str, b: str) -> bool:
    return normalize(a) == normalize(b)


def packages(selectors: list[str]) -> list[Package]:
    roots = sorted(ROOT.glob("book/part-*/ch[0-9][0-9]-*")) + sorted((ROOT / "capstones").glob("capstone-*"))
    if selectors:
        roots = [r for r in roots if any(r.name.startswith(s) for s in selectors)]
    return [Package(r) for r in roots]


def marking_md(m: dict) -> str:
    rows = "\n".join(f"| {c['criterion']} | {c['points']} |" for c in m.get("marking", []))
    return (f"# Marking scheme: {m.get('id')} {m.get('title')}\n\n"
            f"Type {m.get('type')} · kind {m.get('kind')} · tier {m.get('tier')} · {m.get('points')} points\n\n"
            f"**Evidence required:** {m.get('evidence_required', '—')}\n\n"
            f"| Criterion | Points |\n|---|---|\n{rows}\n")


def lab_checks_md(payload: dict) -> str:
    rows = "\n".join(f"| `{k.rstrip(':')}` | {v} |" for k, v in payload["lab_checks"].items())
    return ("# Lab checks this exercise relies on\n\n"
            "When your lab implementation is complete, `check.py` prints these lines (reference run):\n\n"
            f"| Check | Reference line |\n|---|---|\n{rows}\n")


def exercise_readme(ex, files: list[str]) -> str:
    m = ex.meta
    kind = m.get("kind")
    how = {
        "computed": "`result.md` and `result.json` are what the reference `solve.py` printed when it was run "
                    "today; `answer.md` is the worked solution with the method.",
        "written": "`answer.md` is a model answer. Written answers vary: compare your reasoning and evidence "
                   "with it and with the marking scheme, not your wording.",
        "lab": "`lab_checks.md` lists the `check.py` lines this exercise depends on, as a finished lab prints "
               "them; `answer.md` is the worked answer for the parts the checker does not cover.",
    }.get(kind, "")
    listing = "\n".join(f"- `{f}`" for f in files)
    return (f"# Expected outputs: {m.get('id')} {m.get('title')}\n\n"
            "These are the reference results for this exercise, so you can see what a finished answer looks "
            "like and check your own. **Attempt the exercise first**, then compare. Put your own work in "
            "`outputs/` (one level up), not in this folder; this folder is regenerated and would overwrite it.\n\n"
            f"{how}\n\n{listing}\n\n"
            "Numbers carry the evidence labels used in the book: `[MODELED]` and `[ILLUSTRATIVE]` values come "
            "from the stated assumptions and do not change from run to run; `[MEASURED]` values belong to the "
            "machine that produced them.\n\n"
            f"{STAMP}\n")


def lab_readme(pkg: Package, sol_summary: str, starter_summary: str) -> str:
    where = "starter-kit" if pkg.is_capstone else "lab"
    return ("# Expected checker output\n\n"
            f"What `python check.py` prints in `{where}/`, run today:\n\n"
            f"- `check_starter.txt`: the untouched starter, as you will first see it ({starter_summary}). TODO "
            "lines mark the functions you still have to write.\n"
            f"- `check_solution.txt`: a complete reference implementation ({sol_summary}). Your lab is done when "
            "your output matches it check for check. Details after each check name may differ where the "
            "checker reports your own numbers, but every check must PASS (a SKIP is expected where a dataset "
            "generator is not shipped).\n\n"
            f"{STAMP}\n")


def last_line(report: str) -> str:
    lines = [ln for ln in normalize(report).splitlines() if ln.strip()]
    return lines[-1].strip() if lines else "no output"


def main(argv: list[str]) -> int:
    problems: list[str] = []
    counts = {"exercises": 0, "labs": 0}
    for pkg in packages(argv):
        sol_rc, sol_out = run_checker(pkg.checker, "solution")
        st_rc, st_out = run_checker(pkg.checker, "starter")
        gdir = pkg.golden_dir
        for name, text in (("check_solution.txt", sol_out), ("check_starter.txt", st_out)):
            g = gdir / name
            if g.is_file() and not same(text, g.read_text(encoding="utf-8")):
                problems.append(f"{pkg.root.name}: fresh {name} differs from {g.relative_to(ROOT)}")
        if sol_rc != 0:
            problems.append(f"{pkg.root.name}: reference checker exited {sol_rc}")
        if not any(p.startswith(pkg.root.name) for p in problems):
            dest = fresh_dir(pkg.lab_dir / "expected")
            write(dest / "check_solution.txt", normalize(sol_out))
            write(dest / "check_starter.txt", normalize(st_out))
            write(dest / "README.md", lab_readme(pkg, last_line(sol_out), last_line(st_out)))
            counts["labs"] += 1
        if pkg.is_capstone:
            continue
        for ex in pkg.exercises():
            kind = ex.meta.get("kind")
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                files: dict[str, str] = {}
                if kind == "computed":
                    rc, log = run_solver(ex, out)
                    if rc != 0:
                        problems.append(f"{ex.sol_dir.name}: solve.py failed\n{log}")
                        continue
                    for p in sorted(out.rglob("*")):
                        if p.is_file():
                            rel = str(p.relative_to(out)).replace("\\", "/")
                            text = p.read_text(encoding="utf-8")
                            g = ex.outputs_dir / rel
                            if not g.is_file() or not same(text, g.read_text(encoding="utf-8")):
                                problems.append(f"{ex.sol_dir.name}: fresh {rel} differs from the golden output")
                            files[rel] = text
                if kind == "lab":
                    payload = lab_checks_payload(ex, normalize(sol_out))
                    g = ex.outputs_dir / "lab_checks.json"
                    if not g.is_file() or json.loads(g.read_text(encoding="utf-8")) != payload:
                        problems.append(f"{ex.sol_dir.name}: lab checks differ from the golden output")
                    files["lab_checks.md"] = lab_checks_md(payload)
                answer = ex.sol_dir / "solution" / "answer.md"
                if answer.is_file():
                    files["answer.md"] = answer.read_text(encoding="utf-8")
                files["marking.md"] = marking_md(marking_payload(ex))
            if any(p.startswith(ex.sol_dir.name) for p in problems):
                continue
            dest = fresh_dir(ex.learner_dir / "outputs" / "expected")
            for rel, text in files.items():
                write(dest / rel, text)
            write(dest / "README.md", exercise_readme(ex, ["README.md", *files]))
            counts["exercises"] += 1
    print(f"expected outputs written: {counts['exercises']} exercises, {counts['labs']} labs/starter kits")
    if problems:
        print(f"{len(problems)} problem(s); nothing written for these:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
