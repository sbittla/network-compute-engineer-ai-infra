"""17-M3 — Apply the pending-job diagnosis to lab cases P03 and P11 (Chapter 17).

Usage: python solve.py --out DIR
Writes result.json and result.md; asserts the answer key (solutions/exercises-key.md).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8", newline="\n")


def close(value: float, key: float, tol: float, what: str) -> None:
    assert abs(value - key) <= tol, f"{what}: computed {value} vs key {key} (tol {tol})"


PKG = Path(__file__).resolve().parents[4]
DATA = PKG / "lab" / "data"
BLOCKING = {"NoSchedule", "NoExecute"}
UNAVAILABLE = {"DRAIN", "DRAINING", "DRAINED", "DOWN", "FAIL", "MAINT"}


def diagnose(case: dict) -> dict:
    job = case["job"]
    res = job.get("resource", "nvidia.com/gpu")
    per_node, total = int(job["gpus_per_node"]), int(job["gpus_per_node"]) * int(job["nodes"])
    causes, eligible, blocked = set(), {}, {}
    q = case.get("quota")
    if q and q["used"] + total > q["hard"]:
        causes.add("QUOTA_EXHAUSTED")
    for n in case["nodes"]:
        alloc = n.get("allocated", {}).get(res, 0)
        apparent = n.get("physical_gpus", 0) - alloc
        reason = None
        if (not n.get("schedulable", True) or n.get("slurm_state", "").upper().rstrip("*~#") in UNAVAILABLE
                or n.get("lifecycle_state", "schedulable") != "schedulable"):
            reason = "NODE_DRAINED"
        elif n.get("allocatable", {}).get(res, 0) == 0 and n.get("physical_gpus", 0) > 0:
            reason = "DEVICE_PLUGIN_NOT_ADVERTISING"
        elif any(n.get("labels", {}).get(k) != v for k, v in job.get("node_selector", {}).items()):
            reason = "SELECTOR_MISMATCH"
        elif any(t["effect"] in BLOCKING and not any(
                tol.get("key") == t["key"] and tol.get("value") == t.get("value") for tol in job.get("tolerations", []))
                for t in n.get("taints", [])):
            reason = "UNTOLERATED_TAINT"
        if reason is None:
            eligible[n["name"]] = n.get("allocatable", {}).get(res, 0) - alloc
        else:
            blocked[n["name"]] = reason
            if apparent >= per_node:
                causes.add(reason)
    whole = sorted(k for k, v in eligible.items() if v >= per_node)
    if sum(eligible.values()) >= total and len(whole) < int(job["nodes"]):
        causes.add("FRAGMENTATION")
    return {"causes": sorted(causes) or ["NONE_FOUND"], "eligible_free": eligible,
            "eligible_total": sum(eligible.values()), "whole_nodes": whole, "blocked": blocked,
            "requested": total, "quota_after": (q["used"] + total) if q else None,
            "quota_hard": q["hard"] if q else None, "events": case.get("events", [])}


def main(out: Path) -> None:
    cases = {c["case_id"]: c for c in json.loads((DATA / "pending_cases.json").read_text(encoding="utf-8"))}
    p03, p11 = diagnose(cases["P03"]), diagnose(cases["P11"])
    # Key 17-M3: P03 34 free >= 32, one whole node (n17) -> FRAGMENTATION; quota 128 <= 160
    assert p03["causes"] == ["FRAGMENTATION"] and p03["eligible_total"] == 34
    assert p03["whole_nodes"] == ["orion-n17"] and p03["quota_after"] == 128 <= p03["quota_hard"] == 160
    assert list(p03["eligible_free"].values()) == [4, 3, 6, 2, 8, 1, 5, 5]
    # Key 17-M3: P11 eligible 8 + 4 = 12 < 16 -> UNTOLERATED_TAINT (not fragmentation); quota 40 <= 48
    assert p11["causes"] == ["UNTOLERATED_TAINT"] and p11["eligible_total"] == 12
    assert p11["blocked"] == {"orion-n31": "UNTOLERATED_TAINT"} and p11["quota_after"] == 40
    result = {"exercise": "17-M3", "evidence_label": "[SIMULATED]", "inputs": {"data": "lab/data/pending_cases.json"},
              "answer": {"P03": p03, "P11": p11}, "units": {"gpus": "GPUs"}}
    md = f"""
# 17-M3 applied diagnoses `[SIMULATED]`

**P03** {p03['events']}: quota {p03['quota_after']} ≤ {p03['quota_hard']}; eligible free {p03['eligible_total']} ≥ {p03['requested']},
whole nodes {p03['whole_nodes']} → {p03['causes']}

**P11** {p11['events']}: quota {p11['quota_after']} ≤ {p11['quota_hard']}; blocked {p11['blocked']};
eligible free {p11['eligible_total']} < {p11['requested']} → {p11['causes']}
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
