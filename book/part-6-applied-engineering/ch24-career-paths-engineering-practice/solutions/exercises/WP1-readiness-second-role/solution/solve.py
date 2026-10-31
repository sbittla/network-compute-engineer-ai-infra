#!/usr/bin/env python3
"""WP1 — readiness of the sample learner for AI Infrastructure SRE / Operations (mid), Section 24.2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
ROLE, SENIORITY = "sre_ops", "mid"
# Demonstrated levels stated in the WP1 prompt (sample learner, Section 24.2 after evidence rules)
LEVELS = {"observability": 1, "reliability_security": 2, "automation": 3, "scheduling": 1,
          "storage_ckpt": 1, "linux_host": 2, "communication": 3}
CAPSTONE_F_OBSERVABILITY = 3   # part (d)

def write_outputs(out: Path, payload: dict, md_lines: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8", newline="\n")


def main_args() -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    return ap.parse_args().out


def score(role: dict, levels: dict, rules: dict) -> dict:
    rows, num, den, max_gap = [], 0.0, 0, 0
    for c in role["competencies"]:
        t = c["targets"][SENIORITY]
        d = levels.get(c["id"], 0)
        frac = min(d, t) / t
        rows.append({"competency": c["id"], "w": c["weight"], "d": d, "t": t,
                     "fraction": round(frac, 3), "w_x_fraction": round(c["weight"] * frac, 3)})
        num += c["weight"] * frac
        den += c["weight"]
        max_gap = max(max_gap, t - d)
    s = round(100 * num / den, 1)
    if s >= rules["ready_min_score"] and max_gap <= rules["ready_max_gap"]:
        status = "ready"
    elif s >= rules["near_min_score"]:
        status = "near"
    else:
        status = "not_ready"
    plan = sorted(({"competency": r["competency"], "gap": r["t"] - r["d"], "priority": r["w"] * (r["t"] - r["d"])}
                   for r in rows if r["t"] > r["d"]), key=lambda e: (-e["priority"], e["competency"]))
    return {"rows": rows, "sum_w": den, "sum_wf": round(num, 3), "score": s, "status": status,
            "max_gap": max_gap, "plan": plan}


def main() -> None:
    out = main_args()
    m = yaml.safe_load((DATA / "competency_matrices.yaml").read_text(encoding="utf-8"))
    role, rules = m["roles"][ROLE], m["evidence_rules"]
    a = score(role, LEVELS, rules)
    after = dict(LEVELS, observability=CAPSTONE_F_OBSERVABILITY)
    d = score(role, after, rules)

    assert a["sum_w"] == 15 and abs(a["sum_wf"] - 11.5) < 1e-6
    assert abs(a["score"] - 76.7) < 0.05 and a["status"] == "near" and a["max_gap"] == 2
    assert [(p["competency"], p["priority"]) for p in a["plan"]] == [("observability", 6), ("scheduling", 2),
                                                                      ("storage_ckpt", 1)]
    assert abs(d["score"] - 90.0) < 0.05 and d["status"] == "ready" and d["max_gap"] == 1

    payload = {"id": "WP1", "evidence_label": "MODELED",
               "inputs": {"role": ROLE, "seniority": SENIORITY, "levels": LEVELS,
                          "thresholds": {k: rules[k] for k in ("ready_min_score", "near_min_score", "ready_max_gap")}},
               "steps": {"table": a["rows"], "sum_w": a["sum_w"], "sum_w_x_fraction": a["sum_wf"]},
               "answer": {"a_score_pct": a["score"], "b_status": a["status"], "b_max_gap": a["max_gap"],
                          "c_gap_plan": a["plan"], "d_score_pct": d["score"], "d_status": d["status"],
                          "d_max_gap": d["max_gap"]},
               "units": {"score": "% of weighted target"}}
    md = ["# WP1 — SRE / Operations (mid) readiness `[MODELED]`", "",
          "| Competency | w | d | t | min(d,t)/t | w × fraction |", "|---|---|---|---|---|---|"]
    md += [f"| {r['competency']} | {r['w']} | {r['d']} | {r['t']} | {r['fraction']:.3f} | {r['w_x_fraction']:.3f} |"
           for r in a["rows"]]
    md += [f"| total | {a['sum_w']} | | | | {a['sum_wf']:.3f} |", "",
           f"(a) score = 100 × {a['sum_wf']:.3f} / {a['sum_w']} = {a['score']} %",
           f"(b) status {a['status']} (max gap {a['max_gap']})",
           "(c) gap plan: " + ", ".join(f"{p['competency']} ({p['priority']})" for p in a["plan"]),
           f"(d) observability → 3: score {d['score']} %, status {d['status']} (max gap {d['max_gap']})"]
    write_outputs(out, payload, md)


if __name__ == "__main__":
    main()
