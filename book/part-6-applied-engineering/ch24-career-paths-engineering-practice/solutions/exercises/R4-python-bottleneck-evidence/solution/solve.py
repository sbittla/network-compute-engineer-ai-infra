#!/usr/bin/env python3
"""R4 — what the real October 2026 register does and does not say about Python (Section 24.4, Table 24.9)."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
REGISTER = DATA / "job_register_2026-10.csv"   # real, dated register [OBSERVED, 2026-10-30]
PATTERNS = {"python": r"\bpython\b", "kubernetes": r"kubernetes|\bk8s\b", "slurm": r"\bslurm\b",
            "nccl": r"\bnccl\b"}

def write_outputs(out: Path, payload: dict, md_lines: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8", newline="\n")


def main_args() -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    return ap.parse_args().out


def tags(cell: str) -> list[str]:
    return [t.strip().lower() for t in cell.split(";") if t.strip()]


def main() -> None:
    out = main_args()
    with REGISTER.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    n = len(rows)
    counts = {}
    for name, pat in PATTERNS.items():
        req = sum(any(re.search(pat, t) for t in tags(r["required_skills"])) for r in rows)
        either = sum(any(re.search(pat, t) for t in tags(r["required_skills"]) + tags(r["preferred_skills"]))
                     for r in rows)
        counts[name] = {"required": req, "required_or_preferred": either}
    exact_python = sum("python" in tags(r["required_skills"]) for r in rows)
    py_tags = Counter(t for r in rows for t in tags(r["required_skills"]) if re.search(r"\bpython\b", t))
    combined = sum(c for t, c in py_tags.items() if t != "python")
    groups = Counter(r["employer_group"] for r in rows)
    employers = len({r["employer"] for r in rows})
    dates = sorted({r["date_checked"] for r in rows})

    assert n == 42 and employers == 11
    assert counts["python"]["required"] == 23                       # Table 24.9: 23 of 42
    assert exact_python == 9                                        # Table 24.9: exact-tag count 9
    assert counts["kubernetes"]["required"] == 12 and counts["slurm"]["required"] == 5
    assert counts["nccl"]["required"] == 3 and counts["nccl"]["required_or_preferred"] == 8
    assert dates == ["2026-10-30"]

    payload = {"id": "R4", "evidence_label": "OBSERVED, 2026-10-30",
               "inputs": {"register": REGISTER.name, "roles": n, "employers": employers,
                          "employer_groups": dict(sorted(groups.items())), "dates_checked": dates},
               "steps": {"python_tags_in_required": dict(sorted(py_tags.items())),
                         "python_exact_tag": exact_python, "python_inside_combined_tags": combined},
               "answer": {"skill_counts": counts, "python_share_pct": round(100 * counts["python"]["required"] / n, 1)},
               "units": {"counts": "roles (of 42)"}}
    md = ["# R4 — Python in the real register `[OBSERVED, 2026-10-30]`", "",
          f"- Roles: {n} at {employers} employers, all checked on {dates[0]}; groups {dict(sorted(groups.items()))}",
          f"- Python in required lists: {counts['python']['required']} of {n} "
          f"({100 * counts['python']['required'] / n:.1f} %); exact tag 'python' only {exact_python}; "
          f"{combined} inside combined tags",
          f"- Kubernetes {counts['kubernetes']['required']}, Slurm {counts['slurm']['required']}, "
          f"NCCL {counts['nccl']['required']} ({counts['nccl']['required_or_preferred']} counting preferred)",
          "- These are posting frequencies, not scarcity: no applicant or interview data is in the register"]
    write_outputs(out, payload, md)


if __name__ == "__main__":
    main()
