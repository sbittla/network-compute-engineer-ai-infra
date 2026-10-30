#!/usr/bin/env python3
"""Chapter 24 lab — role-readiness self-assessment and job-posting register validator.

REFERENCE IMPLEMENTATION (instructor only).

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
    flags: list[str] = []
    if item.get("competency") not in known:
        return 0, ["UNKNOWN_COMPETENCY"]
    caps = rules["type_caps"]
    level = min(int(item.get("claimed_level", 0)), int(caps.get(item.get("type"), 0)))
    if item.get("type") != "self_assessment" and not str(item.get("artifact") or "").strip():
        level = min(level, rules["no_artifact_cap"])
        flags.append("NO_ARTIFACT")
    if item.get("type") == "lab_l1" and bool(item.get("measured_on_hardware")):
        level = min(level, rules["simulation_claimed_as_measured_cap"])
        flags.append("SIMULATION_CLAIMED_AS_MEASURED")
    if item.get("type") == "production" and not str(item.get("verifier") or "").strip():
        level = min(level, rules["production_unverified_cap"])
        flags.append("PRODUCTION_UNVERIFIED")
    date = parse_date(str(item.get("date") or ""))
    stale = False
    if date is None:
        flags.append("NO_DATE")
        stale = True
    elif (as_of - date).days > rules["stale_after_days"]:
        flags.append("STALE")
        stale = True
    if stale:
        level = max(0, level - rules["stale_penalty"])
    return level, flags


def demonstrated_levels(evidence: list[dict], catalog: dict, rules: dict,
                        as_of: dt.date) -> tuple[dict[str, int], dict[str, list[str]]]:
    """Aggregate evidence into a demonstrated level per catalog competency.

    Returns (levels, flags_by_evidence_id). ``levels`` has every catalog id (default 0); each is the
    max effective level over that competency's evidence. A repeated evidence id is counted once (first
    occurrence) and the repeat is flagged DUPLICATE_EVIDENCE under key "<id>#<position>".
    """
    known = set(catalog)
    levels = {cid: 0 for cid in catalog}
    flags: dict[str, list[str]] = {}
    seen: set[str] = set()
    for pos, item in enumerate(evidence):
        eid = str(item.get("id"))
        if eid in seen:
            flags[f"{eid}#{pos}"] = ["DUPLICATE_EVIDENCE"]
            continue
        seen.add(eid)
        lvl, f = effective_level(item, rules, as_of, known)
        flags[eid] = f
        if "UNKNOWN_COMPETENCY" in f:
            continue
        levels[item["competency"]] = max(levels[item["competency"]], lvl)
    return levels, flags


def readiness(role: dict, seniority: str, levels: dict[str, int], rules: dict) -> dict:
    """Score readiness for one role at one seniority level.

    score = 100 * sum(w * min(d, t) / t) / sum(w) over the role's competencies, where d is the
    demonstrated level and t the target. Status: "ready" if score >= ready_min_score and every gap
    <= ready_max_gap; "near" if score >= near_min_score; else "not_ready".
    Returns {"score": float rounded to 1 dp, "status": str, "max_gap": int}.
    """
    num = den = 0.0
    max_gap = 0
    for comp in role["competencies"]:
        t = comp["targets"][seniority]
        d = levels.get(comp["id"], 0)
        num += comp["weight"] * min(d, t) / t
        den += comp["weight"]
        max_gap = max(max_gap, t - d)
    score = round(100.0 * num / den, 1)
    if score >= rules["ready_min_score"] and max_gap <= rules["ready_max_gap"]:
        status = "ready"
    elif score >= rules["near_min_score"]:
        status = "near"
    else:
        status = "not_ready"
    return {"score": score, "status": status, "max_gap": max_gap}


def gap_plan(role: dict, seniority: str, levels: dict[str, int], catalog: dict, capstones: dict) -> list[dict]:
    """Return the prioritised gap list for a role/seniority.

    One entry per competency with gap = target - demonstrated > 0:
      {"competency", "current", "target", "gap", "priority" (= weight * gap),
       "chapters" (list[int]), "capstones" (list of capstone slugs), "evidence_to_produce"}
    evidence_to_produce: "production" if target >= 4; "capstone, lab_hw or case_study" if target == 3;
    else "lab_l1". Sorted by priority desc, then competency id asc.
    """
    plan = []
    for comp in role["competencies"]:
        cid = comp["id"]
        t = comp["targets"][seniority]
        d = levels.get(cid, 0)
        if t - d <= 0:
            continue
        ev = "production" if t >= 4 else ("capstone, lab_hw or case_study" if t == 3 else "lab_l1")
        plan.append({
            "competency": cid, "current": d, "target": t, "gap": t - d, "priority": comp["weight"] * (t - d),
            "chapters": list(catalog[cid]["chapters"]),
            "capstones": [capstones[c] for c in catalog[cid]["capstones"]],
            "evidence_to_produce": ev,
        })
    plan.sort(key=lambda e: (-e["priority"], e["competency"]))
    return plan


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
    url = str(url or "").strip()
    if not url:
        return ""
    parts = urlsplit(url if "://" in url else "https://" + url)
    return parts.netloc.lower() + parts.path.rstrip("/")


def posting_key(row: dict) -> str:
    """Identity key "employer|job_id" (normalised); "" if either part is empty."""
    emp, jid = normalize_text(row.get("employer")), normalize_text(row.get("job_id"))
    return f"{emp}|{jid}" if emp and jid else ""


def row_issues(row: dict, meta: dict, as_of: dt.date) -> list[str]:
    """Field-level issues for one row (no duplicate logic).

    Codes: MISSING_FIELD:<field> (for each empty required field), BAD_DATE, FUTURE_DATE, BAD_URL
    (non-empty url not starting with https://), BAD_SENIORITY, BAD_STATUS (non-empty value not in the
    allowed list after normalize_text), STALE_ACTIVE (status active and as_of - date_checked >
    stale_active_after_days).
    """
    issues = [f"MISSING_FIELD:{f}" for f in meta["required_fields"] if not str(row.get(f) or "").strip()]
    raw_date = str(row.get("date_checked") or "").strip()
    date = parse_date(raw_date)
    if raw_date and date is None:
        issues.append("BAD_DATE")
    if date is not None and date > as_of:
        issues.append("FUTURE_DATE")
    url = str(row.get("url") or "").strip()
    if url and not url.lower().startswith("https://"):
        issues.append("BAD_URL")
    sen = normalize_text(row.get("seniority"))
    if sen and sen not in meta["allowed_seniority"]:
        issues.append("BAD_SENIORITY")
    status = normalize_text(row.get("status"))
    if status and status not in meta["allowed_status"]:
        issues.append("BAD_STATUS")
    if status == "active" and date is not None and (as_of - date).days > meta["stale_active_after_days"]:
        issues.append("STALE_ACTIVE")
    return issues


def duplicate_clusters(rows: list[dict]) -> list[list[int]]:
    """Group row indices into postings: rows sharing a posting_key OR a normalize_url are the same posting
    (transitively). Empty keys/URLs never match. Returns clusters sorted by smallest index; each cluster
    sorted ascending."""
    parent = list(range(len(rows)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    first: dict[str, int] = {}
    for i, row in enumerate(rows):
        for tag, val in (("k", posting_key(row)), ("u", normalize_url(row.get("url")))):
            if not val:
                continue
            if (tag, val) in first:
                union(first[(tag, val)], i)
            else:
                first[(tag, val)] = i
    groups: dict[int, list[int]] = {}
    for i in range(len(rows)):
        groups.setdefault(find(i), []).append(i)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: g[0])


def representative(cluster: list[int], rows: list[dict]) -> int:
    """Pick the row kept for a cluster: latest valid date_checked; ties (or no valid dates) -> lowest index."""
    def key(i: int) -> tuple:
        d = parse_date(rows[i].get("date_checked"))
        return (d is not None, d or dt.date.min, -i)
    return max(cluster, key=key)


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
    as_of = parse_date(str(meta["as_of"]))
    issues: dict[int, list[str]] = {}
    for i, row in enumerate(rows):
        codes = row_issues(row, meta, as_of)
        if codes:
            issues[i] = codes
    clusters = duplicate_clusters(rows)
    reps = []
    for cl in clusters:
        rep = representative(cl, rows)
        reps.append(rep)
        for i in cl:
            if i != rep:
                issues.setdefault(i, []).append(f"DUPLICATE_OF:{rep}")
    reps.sort()
    blocking = ("MISSING_FIELD", "BAD_", "FUTURE_DATE")
    complete = [r for r in reps if not any(c.startswith(blocking) for c in issues.get(r, []))]
    active_fresh = [r for r in complete
                    if normalize_text(rows[r].get("status")) == "active" and "STALE_ACTIVE" not in issues.get(r, [])]
    counts: Counter = Counter()
    for codes in issues.values():
        for c in codes:
            counts["DUPLICATE" if c.startswith("DUPLICATE_OF") else c] += 1
    return {"issues": issues, "clusters": clusters, "representatives": reps, "complete": complete,
            "active_fresh": active_fresh, "issue_counts": counts}


def skill_frequency(rows: list[dict], indices: list[int]) -> list[tuple[str, int]]:
    """Count required skills (split on ';', normalize_text, drop empties) over the given rows.
    Returns [(skill, count)] sorted by count desc then skill asc."""
    c: Counter = Counter()
    for i in indices:
        for s in str(rows[i].get("required_skills") or "").split(";"):
            s = normalize_text(s)
            if s:
                c[s] += 1
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))


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
