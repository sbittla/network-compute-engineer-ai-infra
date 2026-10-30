#!/usr/bin/env python3
"""Checker for the Chapter 24 lab (role readiness + job-posting register validator).

Usage:
    python check.py                    # checks starter/career_lab.py (your work)
    python check.py --impl solution    # checks ../solutions/lab/career_lab.py (reference)

Prints one PASS/FAIL/TODO line per check. Exit code 0 only when every check passes.
No hardware, no network access, no root; finishes in a few seconds.
"""
from __future__ import annotations

import argparse
import datetime as dt
import filecmp
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def load_impl(impl: str):
    path = (HERE / "starter" / "career_lab.py") if impl == "starter" else \
        (HERE.parent / "solutions" / "lab" / "career_lab.py")
    if not path.exists():
        raise SystemExit(f"FAIL load: {path} not found")
    spec = importlib.util.spec_from_file_location(f"career_lab_{impl}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class CheckSkipped(Exception):
    """Raised when a check cannot run in this distribution (instructor-only generator absent)."""


class CheckFailed(Exception):
    pass


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise CheckFailed(msg)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impl", choices=["starter", "solution"], default="starter")
    args = ap.parse_args()
    m = load_impl(args.impl)

    matrices = m.load_yaml(DATA / "competency_matrices.yaml")
    evidence = m.load_yaml(DATA / "learner_evidence.yaml")
    meta = m.load_yaml(DATA / "register_meta.yaml")
    rows = m.load_register(DATA / "job_register.csv")
    rules = matrices["evidence_rules"]
    catalog = matrices["catalog"]
    roles = matrices["roles"]
    as_of = dt.date(2026, 10, 15)
    known = set(catalog)

    results: list[tuple[str, str, str]] = []

    def run(name: str, fn: Callable[[], str | None]) -> None:
        try:
            note = fn() or ""
            results.append(("PASS", name, note))
        except CheckSkipped as exc:
            results.append(("SKIP", name, str(exc)))
        except NotImplementedError as exc:
            results.append(("TODO", name, f"not implemented: {exc}"))
        except CheckFailed as exc:
            results.append(("FAIL", name, str(exc)))
        except Exception as exc:  # noqa: BLE001 - report, never crash
            results.append(("FAIL", name, f"{type(exc).__name__}: {exc}"))

    # ---------------------------------------------------------------- data integrity
    def c_data() -> str:
        gen = HERE / "tools" / "generate_data.py"
        if not gen.exists():
            raise CheckSkipped("generator not shipped in the student release (instructor copy only)")
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, str(HERE / "tools" / "generate_data.py"), "--out", tmp],
                                  capture_output=True, text=True, timeout=60)
            expect(proc.returncode == 0, f"generator failed: {proc.stderr.strip()[-200:]}")
            for f in ("competency_matrices.yaml", "learner_evidence.yaml", "job_register.csv", "register_meta.yaml"):
                expect(filecmp.cmp(DATA / f, Path(tmp) / f, shallow=False), f"data/{f} differs from generator output")
        return "data/ is byte-identical to tools/generate_data.py output"
    run("data_regenerates", c_data)

    # ---------------------------------------------------------------- Part A
    def item(**kw) -> dict:
        base = {"id": "T", "competency": "congestion", "type": "capstone", "claimed_level": 3,
                "artifact": "x.md", "date": "2026-09-01", "verifier": "", "measured_on_hardware": False}
        base.update(kw)
        return base

    def c_effective() -> str:
        cases = [
            (item(), 3, []),
            (item(type="course", claimed_level=4), 1, []),
            (item(type="lab_l1", claimed_level=3), 2, []),
            (item(artifact=""), 1, ["NO_ARTIFACT"]),
            (item(type="self_assessment", artifact="", claimed_level=4), 1, []),
            (item(type="lab_l1", claimed_level=2, measured_on_hardware=True), 1, ["SIMULATION_CLAIMED_AS_MEASURED"]),
            (item(type="production", claimed_level=4), 3, ["PRODUCTION_UNVERIFIED"]),
            (item(type="production", claimed_level=4, verifier="lead"), 4, []),
            (item(date="2023-01-01"), 2, ["STALE"]),
            (item(date="2023-10-16"), 3, []),          # 1,095 days old: not yet stale
            (item(date="2023-10-15"), 2, ["STALE"]),   # 1,096 days old: stale
            (item(date=""), 2, ["NO_DATE"]),
            (item(type="production", claimed_level=4, date="2020-01-01"), 2, ["PRODUCTION_UNVERIFIED", "STALE"]),
            (item(competency="bgp_evpn"), 0, ["UNKNOWN_COMPETENCY"]),
        ]
        for i, (it, lvl, flags) in enumerate(cases):
            got_lvl, got_flags = m.effective_level(it, rules, as_of, known)
            expect(got_lvl == lvl and sorted(got_flags) == sorted(flags),
                   f"case {i} ({it['type']}, claimed {it['claimed_level']}, date {it['date']!r}): "
                   f"expected ({lvl}, {flags}), got ({got_lvl}, {got_flags})")
        return f"{len(cases)} rule cases"
    run("effective_level_rules", c_effective)

    def c_demonstrated() -> str:
        levels, flags = m.demonstrated_levels(evidence["evidence"], catalog, rules, as_of)
        expect(set(levels) == known, "levels must contain every catalog competency")
        want = {"l3_fabric": 4, "rdma_fabrics": 3, "congestion": 2, "physical_layer": 2, "host_topology": 2,
                "observability": 1, "automation": 3, "communication": 3, "collectives": 2, "storage_ckpt": 1,
                "linux_host": 2, "scheduling": 1, "gpu_compute": 0, "reliability_security": 2, "inference": 0}
        for k, v in want.items():
            expect(levels[k] == v, f"{k}: expected demonstrated level {v}, got {levels[k]}")
        flat = sorted(f for fl in flags.values() for f in fl)
        expect(flat == sorted(["SIMULATION_CLAIMED_AS_MEASURED", "STALE", "PRODUCTION_UNVERIFIED", "STALE",
                               "NO_ARTIFACT", "DUPLICATE_EVIDENCE", "UNKNOWN_COMPETENCY", "STALE", "NO_DATE"]),
               f"unexpected flag set: {flat}")
        return "15 competency levels and 9 evidence flags match"
    run("demonstrated_levels", c_demonstrated)

    def c_readiness() -> str:
        levels, _ = m.demonstrated_levels(evidence["evidence"], catalog, rules, as_of)
        want = {("ai_network", "junior"): (100.0, "ready"), ("ai_network", "mid"): (94.1, "ready"),
                ("ai_network", "senior"): (78.4, "near"), ("ai_network", "staff"): (69.6, "not_ready"),
                ("sre_ops", "mid"): (76.7, "near"), ("gpu_hpc", "senior"): (48.9, "not_ready"),
                ("cluster_platform", "junior"): (80.0, "near")}
        for (rid, sen), (score, status) in want.items():
            r = m.readiness(roles[rid], sen, levels, rules)
            expect(abs(r["score"] - score) < 0.05 and r["status"] == status,
                   f"{rid}/{sen}: expected {score} {status}, got {r['score']} {r['status']}")
        # status logic: high score but one gap of 2 must not be "ready"
        role = {"competencies": [{"id": "a", "weight": 9, "targets": {"senior": 3}},
                                 {"id": "b", "weight": 1, "targets": {"senior": 3}}]}
        r = m.readiness(role, "senior", {"a": 3, "b": 1}, rules)
        expect(r["status"] == "near" and r["max_gap"] == 2 and abs(r["score"] - 93.3) < 0.05,
               f"score 93.3 with a gap of 2 must be 'near', got {r}")
        return "7 role/seniority scores + gap-blocks-ready rule"
    run("readiness_scores", c_readiness)

    def c_gap() -> str:
        levels, _ = m.demonstrated_levels(evidence["evidence"], catalog, rules, as_of)
        plan = m.gap_plan(roles["ai_network"], "senior", levels, catalog, matrices["capstones"])
        got = [(g["competency"], g["gap"], g["priority"]) for g in plan]
        want = [("observability", 2, 4), ("congestion", 1, 3), ("host_topology", 1, 2), ("physical_layer", 1, 2)]
        expect(got == want, f"expected {want}, got {got}")
        expect(plan[0]["capstones"] == ["capstone-b-network-telemetry-troubleshooting",
                                        "capstone-f-reliability-game-day"], "observability capstones wrong")
        expect(plan[0]["evidence_to_produce"] == "capstone, lab_hw or case_study", "evidence_to_produce wrong")
        staff = m.gap_plan(roles["ai_network"], "staff", levels, catalog, matrices["capstones"])
        expect(staff[0]["competency"] == "congestion" and staff[0]["priority"] == 6 and
               any(g["evidence_to_produce"] == "production" for g in staff), "staff plan ordering/evidence wrong")
        return "ai_network/senior plan: " + ", ".join(f"{c}({p})" for c, _, p in got)
    run("gap_plan_priorities", c_gap)

    # ---------------------------------------------------------------- Part B
    def c_url_key() -> str:
        cases = {
            "https://careers.example.com/a/jobs/X1": "careers.example.com/a/jobs/X1",
            "HTTPS://Careers.Example.COM/a/jobs/X1/?utm_source=board#apply": "careers.example.com/a/jobs/X1",
            "http://careers.example.com/a/jobs/X1/": "careers.example.com/a/jobs/X1",
            "": "",
        }
        for u, want in cases.items():
            expect(m.normalize_url(u) == want, f"normalize_url({u!r}) -> {m.normalize_url(u)!r}, want {want!r}")
        expect(m.posting_key({"employer": "  VANTOR   Cloud ", "job_id": "syn-van-1"}) == "vantor cloud|syn-van-1",
               "posting_key must casefold and collapse whitespace")
        expect(m.posting_key({"employer": "Vantor Cloud", "job_id": " "}) == "", "empty job_id -> empty key")
        return "URL canonicalisation and identity key"
    run("normalize_url_and_key", c_url_key)

    def c_row_issues() -> str:
        good = {"employer": "E", "title": "T", "job_id": "J", "location": "L", "seniority": "Senior",
                "url": "https://careers.example.com/e/j", "date_checked": "2026-10-01",
                "required_skills": "bgp", "status": "active"}
        expect(m.row_issues(good, meta, as_of) == [], f"clean row flagged: {m.row_issues(good, meta, as_of)}")
        tests = [
            ({"job_id": ""}, {"MISSING_FIELD:job_id"}),
            ({"date_checked": "01/10/2026"}, {"BAD_DATE"}),
            ({"date_checked": "2026-10-20"}, {"FUTURE_DATE"}),
            ({"url": "http://careers.example.com/e/j"}, {"BAD_URL"}),
            ({"seniority": "Sr."}, {"BAD_SENIORITY"}),
            ({"status": "open"}, {"BAD_STATUS"}),
            ({"date_checked": "2026-09-14"}, {"STALE_ACTIVE"}),
            ({"date_checked": "2026-09-15"}, set()),
            ({"date_checked": "2026-05-01", "status": "archived"}, set()),
        ]
        for change, want in tests:
            got = set(m.row_issues(dict(good, **change), meta, as_of))
            expect(got == want, f"{change}: expected {sorted(want)}, got {sorted(got)}")
        return f"{len(tests) + 1} field-rule cases"
    run("row_issues_rules", c_row_issues)

    def c_clusters() -> str:
        toy = [
            {"employer": "A", "job_id": "1", "url": "https://x.example.com/1"},
            {"employer": "a ", "job_id": "1", "url": "https://x.example.com/req/9"},   # same key as 0
            {"employer": "A", "job_id": "2", "url": "https://x.example.com/req/9/"},  # same URL as 1
            {"employer": "A", "job_id": "", "url": ""},                               # never matches
            {"employer": "A", "job_id": "", "url": ""},
        ]
        got = m.duplicate_clusters(toy)
        expect(got == [[0, 1, 2], [3], [4]], f"transitive clustering wrong: {got}")
        cl = m.duplicate_clusters(rows)
        multi = [c for c in cl if len(c) > 1]
        expect(len(cl) == 51 and len(multi) == 9, f"expected 51 postings / 9 duplicate groups, got {len(cl)} / {len(multi)}")
        expect([1, 31, 35] in cl, "the planted three-row chain (key then URL) was not merged")
        return "transitive merge; 61 rows -> 51 postings"
    run("duplicate_clusters", c_clusters)

    def c_rep() -> str:
        toy = [{"date_checked": "2026-10-01"}, {"date_checked": "2026-10-03"}, {"date_checked": "bad"},
               {"date_checked": "2026-10-03"}]
        expect(m.representative([0, 1, 2, 3], toy) == 1, "latest valid date, tie -> lowest index")
        expect(m.representative([2], toy) == 2, "singleton cluster")
        want = {(1, 31, 35): 35, (3, 27): 27, (15, 42): 15, (37, 59): 37, (54, 55): 54}
        for cl, rep in want.items():
            got = m.representative(list(cl), rows)
            expect(got == rep, f"cluster {cl}: expected representative {rep}, got {got}")
        return "representative selection"
    run("representative_selection", c_rep)

    def c_validate() -> str:
        res = m.validate_register(rows, meta)
        expect(len(res["representatives"]) == 51, f"unique postings {len(res['representatives'])} != 51")
        expect(len(res["complete"]) == 40, f"complete postings {len(res['complete'])} != 40")
        expect(len(res["active_fresh"]) == 31, f"active & fresh postings {len(res['active_fresh'])} != 31")
        want = {"DUPLICATE": 10, "STALE_ACTIVE": 3, "BAD_DATE": 1, "FUTURE_DATE": 1, "BAD_URL": 1,
                "BAD_SENIORITY": 1, "BAD_STATUS": 1, "MISSING_FIELD:job_id": 2, "MISSING_FIELD:date_checked": 1,
                "MISSING_FIELD:url": 1, "MISSING_FIELD:required_skills": 1, "MISSING_FIELD:seniority": 1,
                "MISSING_FIELD:location": 1}
        got = dict(res["issue_counts"])
        expect(got == want, f"issue counts differ: got {got}")
        expect("DUPLICATE_OF:37" in res["issues"].get(59, []), "row 59 should be DUPLICATE_OF:37")
        return "51 unique / 40 complete / 31 active-fresh; 25 issues"
    run("validate_register", c_validate)

    def c_skills() -> str:
        res = m.validate_register(rows, meta)
        top = m.skill_frequency(rows, res["active_fresh"])[:5]
        want = [("python", 27), ("kubernetes", 12), ("inference serving", 7), ("nccl", 7), ("traffic generators", 7)]
        expect(top == want, f"top skills {top} != {want}")
        return "top-5 required skills over active, fresh, complete postings"
    run("skill_frequency", c_skills)

    width = max(len(n) for _, n, _ in results)
    for status, name, note in results:
        print(f"{status:4} {name:<{width}}  {note}")
    passed = sum(s == "PASS" for s, _, _ in results)
    skipped = sum(s == "SKIP" for s, _, _ in results)
    print(f"\n{passed}/{len(results) - skipped} checks passed ({args.impl}); {skipped} skipped")
    return 0 if passed + skipped == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
