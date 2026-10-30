#!/usr/bin/env python3
"""Chapter 24 lab — role-readiness self-assessment and job-posting register validator.

STARTER: implement every function that raises NotImplementedError.
Run ``python ../check.py`` to see your progress.

Part A scores a learner's evidence portfolio against role competency matrices
(``data/competency_matrices.yaml``) and emits a prioritised gap plan.
Part B validates and deduplicates a SYNTHETIC job-posting register (``data/job_register.csv``).

All levels are on the 0-4 proficiency scale; readiness scores are percentages (0-100).
Dates are ISO-8601 calendar dates.

Usage:
    python career_lab.py --data ../../lab/data --role ai_network --seniority senior
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import yaml

# ============================================================================================
# Loading helpers (provided; identical in starter)
# ============================================================================================


def load_yaml(path: Path) -> dict:
    """Load a YAML document from ``path``."""
    with Path(path).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_register(path: Path) -> list[dict]:
    """Load the job register CSV as a list of row dicts (all values are strings)."""
    with Path(path).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_date(value: str | None) -> dt.date | None:
    """Return a date for a strict ISO ``YYYY-MM-DD`` string, else None."""
    if not value or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        return None
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        return None


# ============================================================================================
# Part A — role-readiness self-assessment
# ============================================================================================


def effective_level(item: dict, rules: dict, as_of: dt.date, known: set[str]) -> tuple[int, list[str]]:
    """Return (effective proficiency level 0-4, flags) for one evidence item.

    Rules, applied in this order:
      1. Unknown competency id -> (0, ["UNKNOWN_COMPETENCY"]).
      2. level = min(claimed_level, type_caps[type]).
      3. Missing artifact (and type != self_assessment) -> cap at no_artifact_cap, flag NO_ARTIFACT.
      4. measured_on_hardware true for a lab_l1 item -> cap at simulation_claimed_as_measured_cap,
         flag SIMULATION_CLAIMED_AS_MEASURED.
      5. type production with empty verifier -> cap at production_unverified_cap, flag PRODUCTION_UNVERIFIED.
      6. Missing/invalid date -> flag NO_DATE and treat as stale. Age > stale_after_days -> flag STALE.
         Stale items lose stale_penalty levels (floor 0).
    """
    # TODO: Apply rules 1-6 in order; collect flags; return (level, flags).
    raise NotImplementedError("effective_level")


def demonstrated_levels(evidence: list[dict], catalog: dict, rules: dict,
                        as_of: dt.date) -> tuple[dict[str, int], dict[str, list[str]]]:
    """Aggregate evidence into a demonstrated level per catalog competency.

    Returns (levels, flags_by_evidence_id). ``levels`` has every catalog id (default 0); each is the
    max effective level over that competency's evidence. A repeated evidence id is counted once (first
    occurrence) and the repeat is flagged DUPLICATE_EVIDENCE under key "<id>#<position>".
    """
    # TODO: Loop evidence; skip and flag repeated ids; take max effective level per competency.
    raise NotImplementedError("demonstrated_levels")


def readiness(role: dict, seniority: str, levels: dict[str, int], rules: dict) -> dict:
    """Score readiness for one role at one seniority level.

    score = 100 * sum(w * min(d, t) / t) / sum(w) over the role's competencies, where d is the
    demonstrated level and t the target. Status: "ready" if score >= ready_min_score and every gap
    <= ready_max_gap; "near" if score >= near_min_score; else "not_ready".
    Returns {"score": float rounded to 1 dp, "status": str, "max_gap": int}.
    """
    # TODO: Weighted coverage score, max gap, and status thresholds from rules.
    raise NotImplementedError("readiness")


def gap_plan(role: dict, seniority: str, levels: dict[str, int], catalog: dict, capstones: dict) -> list[dict]:
    """Return the prioritised gap list for a role/seniority.

    One entry per competency with gap = target - demonstrated > 0:
      {"competency", "current", "target", "gap", "priority" (= weight * gap),
       "chapters" (list[int]), "capstones" (list of capstone slugs), "evidence_to_produce"}
    evidence_to_produce: "production" if target >= 4; "capstone, lab_hw or case_study" if target == 3;
    else "lab_l1". Sorted by priority desc, then competency id asc.
    """
    # TODO: Build one entry per positive gap; sort by (-priority, competency).
    raise NotImplementedError("gap_plan")


# ============================================================================================
# Part B — job-posting register validator
# ============================================================================================


def normalize_text(value: str | None) -> str:
    """Casefold and collapse internal whitespace; None -> ""."""
    return " ".join(str(value or "").split()).casefold()


def normalize_url(url: str | None) -> str:
    """Canonical posting URL for duplicate detection.

    Lowercase the host, drop scheme, query string, fragment and trailing slash; keep path case.
    "" for empty input. e.g. "HTTPS://Careers.Example.COM/a/jobs/X/?utm_source=y" -> "careers.example.com/a/jobs/X"
    """
    # TODO: Use urllib.parse.urlsplit; lowercase netloc; drop query/fragment/trailing slash.
    raise NotImplementedError("normalize_url")


def posting_key(row: dict) -> str:
    """Identity key "employer|job_id" (normalised); "" if either part is empty."""
    # TODO: Combine normalize_text(employer) and normalize_text(job_id).
    raise NotImplementedError("posting_key")


def row_issues(row: dict, meta: dict, as_of: dt.date) -> list[str]:
    """Field-level issues for one row (no duplicate logic).

    Codes: MISSING_FIELD:<field> (for each empty required field), BAD_DATE, FUTURE_DATE, BAD_URL
    (non-empty url not starting with https://), BAD_SENIORITY, BAD_STATUS (non-empty value not in the
    allowed list after normalize_text), STALE_ACTIVE (status active and as_of - date_checked >
    stale_active_after_days).
    """
    # TODO: Check required fields, date format/future, https, allowed seniority/status, stale active.
    raise NotImplementedError("row_issues")


def duplicate_clusters(rows: list[dict]) -> list[list[int]]:
    """Group row indices into postings: rows sharing a posting_key OR a normalize_url are the same posting
    (transitively). Empty keys/URLs never match. Returns clusters sorted by smallest index; each cluster
    sorted ascending."""
    # TODO: Union-find (or BFS) over shared keys and shared normalised URLs.
    raise NotImplementedError("duplicate_clusters")


def representative(cluster: list[int], rows: list[dict]) -> int:
    """Pick the row kept for a cluster: latest valid date_checked; ties (or no valid dates) -> lowest index."""
    # TODO: max() over the cluster with a key of (has valid date, date, -index).
    raise NotImplementedError("representative")


def validate_register(rows: list[dict], meta: dict) -> dict:
    """Validate and deduplicate the register.

    Returns {
      "issues": {row_index: [codes]} for rows with >= 1 code; duplicates (non-representatives) get
                "DUPLICATE_OF:<rep index>",
      "clusters": duplicate_clusters(rows),
      "representatives": sorted list of representative indices,
      "complete": sorted reps with no MISSING_FIELD/BAD_*/FUTURE_DATE codes,
      "active_fresh": sorted complete reps whose status is active and not STALE_ACTIVE,
      "issue_counts": Counter of codes (MISSING_FIELD:* counted per field, DUPLICATE_OF counted as "DUPLICATE"),
    }
    """
    # TODO: Combine row_issues, duplicate_clusters and representative; compute complete/active_fresh/counts.
    raise NotImplementedError("validate_register")


def skill_frequency(rows: list[dict], indices: list[int]) -> list[tuple[str, int]]:
    """Count required skills (split on ';', normalize_text, drop empties) over the given rows.
    Returns [(skill, count)] sorted by count desc then skill asc."""
    # TODO: collections.Counter over normalised required skills.
    raise NotImplementedError("skill_frequency")


# ============================================================================================
# Report (provided)
# ============================================================================================


def render_report(data_dir: Path, role_id: str, seniority: str) -> str:
    """Render the Markdown readiness + register report used as the lab deliverable."""
    m = load_yaml(data_dir / "competency_matrices.yaml")
    ev = load_yaml(data_dir / "learner_evidence.yaml")
    meta = load_yaml(data_dir / "register_meta.yaml")
    rows = load_register(data_dir / "job_register.csv")
    rules = m["evidence_rules"]
    as_of = parse_date(str(ev["learner"]["as_of"]))
    levels, flags = demonstrated_levels(ev["evidence"], m["catalog"], rules, as_of)
    out = [f"# Role-readiness report - {ev['learner']['name']}", "",
           f"As of {as_of}; evidence class: self-assessment against teaching matrices (not a hiring decision).", "",
           "## Readiness by role", "", "| Role | " + " | ".join(rules["seniority_levels"]) + " |",
           "|---|" + "---|" * len(rules["seniority_levels"])]
    for rid, role in m["roles"].items():
        cells = []
        for s in rules["seniority_levels"]:
            r = readiness(role, s, levels, rules)
            cells.append(f"{r['score']:.1f} ({r['status']})")
        out.append(f"| {role['title']} | " + " | ".join(cells) + " |")
    out += ["", f"## Gap plan - {m['roles'][role_id]['title']} ({seniority})", "",
            "| Priority | Competency | Current -> target | Produce | Chapters | Capstones |", "|---|---|---|---|---|---|"]
    for g in gap_plan(m["roles"][role_id], seniority, levels, m["catalog"], m["capstones"]):
        out.append(f"| {g['priority']} | {g['competency']} | {g['current']} -> {g['target']} | {g['evidence_to_produce']} "
                   f"| {', '.join(map(str, g['chapters']))} | {', '.join(g['capstones'])} |")
    out += ["", "## Evidence flags", ""]
    out += [f"- {k}: {', '.join(v)}" for k, v in flags.items() if v]
    res = validate_register(rows, meta)
    out += ["", "## Job-posting register (SYNTHETIC)", "",
            f"- rows: {len(rows)}; unique postings: {len(res['representatives'])}; complete: {len(res['complete'])}; "
            f"active and fresh: {len(res['active_fresh'])}",
            "- issue counts: " + ", ".join(f"{k}={v}" for k, v in sorted(res["issue_counts"].items())),
            "- top required skills (active, fresh, complete): "
            + ", ".join(f"{s} ({n})" for s, n in skill_frequency(rows, res["active_fresh"])[:8])]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "lab" / "data")
    ap.add_argument("--role", default="ai_network")
    ap.add_argument("--seniority", default="senior")
    ap.add_argument("--out", type=Path, default=None, help="write Markdown report here (default: stdout)")
    args = ap.parse_args()
    try:
        report = render_report(args.data, args.role, args.seniority)
    except NotImplementedError as exc:
        raise SystemExit(f"TODO: implement {exc} first (run ../check.py to see which functions remain)")
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":
    main()
