"""Shared helpers for the in-container lab harness (test_package.py, generate_outputs.py, run_lab.py).

A *package* is one chapter folder (book/part-*/chNN-*) or one capstone folder (capstones/capstone-*).
Layout conventions are documented in docs/LAB_STANDARDS.md ("Containers" and "Exercise folders").
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

EXERCISE_KINDS = {"computed", "written", "lab"}
EXERCISE_TYPES = {
    "knowledge-check", "worked-problem", "hands-on-lab", "outline-mandated",
    "troubleshooting", "design-challenge", "reflection", "deliverable",
}
META_REQUIRED = ("id", "title", "folder", "type", "difficulty", "tier", "kind", "points",
                 "evidence_required", "marking")
PROMPT_START = "<!-- prompt:start -->"
PROMPT_END = "<!-- prompt:end -->"
CHECK_TIMEOUT_S = 300


@dataclass
class Package:
    root: Path

    @property
    def is_capstone(self) -> bool:
        return (self.root / "starter-kit").is_dir()

    @property
    def lab_dir(self) -> Path:
        return self.root / ("starter-kit" if self.is_capstone else "lab")

    @property
    def checker(self) -> Path:
        return self.lab_dir / "check.py"

    @property
    def golden_dir(self) -> Path:
        """Committed reference outputs of the lab checker (instructor-only)."""
        return self.root / ("instructor" if self.is_capstone else "solutions") / ("outputs" if self.is_capstone else "lab/outputs")

    @property
    def exercises_dir(self) -> Path:
        return self.root / "exercises"

    @property
    def exercise_solutions_dir(self) -> Path:
        return self.root / "solutions" / "exercises"

    def exercises(self) -> list["Exercise"]:
        base = self.exercise_solutions_dir
        if not base.is_dir():
            return []
        return [Exercise(self, d) for d in sorted(p for p in base.iterdir() if (p / "meta.yaml").is_file())]


@dataclass
class Exercise:
    pkg: Package
    sol_dir: Path
    meta: dict = field(init=False)

    def __post_init__(self) -> None:
        self.meta = yaml.safe_load((self.sol_dir / "meta.yaml").read_text(encoding="utf-8")) or {}

    @property
    def name(self) -> str:
        return self.sol_dir.name

    @property
    def learner_dir(self) -> Path:
        return self.pkg.exercises_dir / self.sol_dir.name

    @property
    def outputs_dir(self) -> Path:
        return self.sol_dir / "outputs"

    @property
    def solve_script(self) -> Path:
        return self.sol_dir / "solution" / "solve.py"


def normalize(text: str) -> str:
    """Make checker/solver output comparable across runs: LF endings, no timings, temp paths or PIDs."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\bin \d+(?:\.\d+)? ?s\b", "in <t> s", text)
    text = re.sub(r"\(\d+(?:\.\d+)? ?s([,)])", r"(<t>s\1", text)
    text = re.sub(r"(?:/tmp|/var/tmp)/[^\s'\"),]+", "<tmp>", text)
    text = re.sub(r"\bpids? \d+(?:, \d+)*", "pids <n>", text)  # process IDs differ between hosts
    return "\n".join(line.rstrip() for line in text.split("\n")).strip() + "\n"


def run_checker(checker: Path, impl: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(checker), "--impl", impl],
        cwd=checker.parent, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=CHECK_TIMEOUT_S,
    )
    return proc.returncode, proc.stdout + proc.stderr


def run_solver(ex: Exercise, out_dir: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(ex.solve_script), "--out", str(out_dir)],
        cwd=ex.solve_script.parent, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=CHECK_TIMEOUT_S,
    )
    return proc.returncode, proc.stdout + proc.stderr


def check_lines(report: str) -> dict[str, str]:
    """Map check name -> full report line, for lines like 'PASS name  reason' or 'PASS 11 name ...'."""
    found: dict[str, str] = {}
    for line in report.splitlines():
        m = re.match(r"^\s*(PASS|FAIL|SKIP|TODO)\s+(.*)$", line)
        if m:
            found[m.group(2).strip()] = line.strip()
    return found


def marking_payload(ex: Exercise) -> dict:
    m = ex.meta
    return {
        "id": m.get("id"),
        "title": m.get("title"),
        "type": m.get("type"),
        "difficulty": m.get("difficulty"),
        "tier": m.get("tier"),
        "kind": m.get("kind"),
        "points": m.get("points"),
        "evidence_required": m.get("evidence_required"),
        "marking": m.get("marking"),
        "lab_checks": m.get("lab_checks", []),
    }


def lab_checks_payload(ex: Exercise, solution_report: str) -> dict:
    lines = check_lines(solution_report)
    result = {}
    for name in ex.meta.get("lab_checks", []):
        bare = name.rstrip(":")  # checkers print "name: reason" or "name  reason"; accept either spelling
        hit = next((line for key, line in lines.items() if key in (name, bare) or key.startswith(bare + " ")
                    or key.startswith(bare + ":") or re.match(rf"^\d+\s+{re.escape(bare)}\b", key)), None)
        result[name] = hit
    return {"id": ex.meta.get("id"), "lab_checks": result}


def dump_json(obj: object) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def prompt_block(readme: str) -> str | None:
    if PROMPT_START not in readme or PROMPT_END not in readme:
        return None
    return readme.split(PROMPT_START, 1)[1].split(PROMPT_END, 1)[0]


def squash(text: str) -> str:
    """Whitespace- and markdown-emphasis-insensitive form used to compare a prompt with exercises.md."""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\]\([^)]*\)", "]", text)  # link targets may be re-based for the exercise folder
    text = re.sub(r"[*_`>|]", "", text)
    return re.sub(r"\s+", " ", text).strip()
