"""17-M2 — Before/after replay of the urgent-eval QOS rule (Chapter 17).

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


import importlib.util

PKG = Path(__file__).resolve().parents[4]          # chapter folder
DATA = PKG / "lab" / "data"


def load_sim():
    spec = importlib.util.spec_from_file_location("orion_sched_ref", PKG / "solutions" / "lab" / "orion_sched.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def summarize(out_sched: dict) -> dict:
    rows = {}
    for jid in out_sched["order"]:
        r = out_sched["results"][jid]
        rows[jid] = sorted(r["nodes"]) if r["status"] == "placed" else r["reason"]
    placed = sum(sum(len(v) for v in r["nodes"].values()) for r in out_sched["results"].values() if r["status"] == "placed")
    return {"order": out_sched["order"], "results": rows, "gpus_placed": placed, "tenant_used": out_sched["tenant_used"]}


def main(out: Path) -> None:
    sim = load_sim()
    cluster = sim.load_json(DATA / "cluster_state.json")
    jobs = sim.load_json(DATA / "job_queue.json")
    before_jobs = [dict(j, priority=100) if j["job_id"] == "J01" else dict(j) for j in jobs]
    after_jobs = [dict(j, priority=110) if j["job_id"] == "J05" else dict(j) for j in before_jobs]
    before = summarize(sim.schedule(cluster, before_jobs))
    after = summarize(sim.schedule(cluster, after_jobs))
    start = sim.build_state(cluster)["tenants"]
    new = {name: {t: s["tenant_used"][t] - start[t]["used"] for t in sorted(start)}
           for name, s in (("before", before), ("after", after))}

    assert before["results"]["J05"] == "InsufficientCapacity" and before["results"]["J08"] == "InsufficientCapacity"
    assert after["results"]["J05"] == ["orion-n22", "orion-n24"]
    assert after["results"]["J08"] == ["orion-n13", "orion-n18"]
    assert after["results"]["J01"] == "InsufficientCapacity"
    assert before["gpus_placed"] == after["gpus_placed"] == 69
    assert new["before"]["research"] == 0 and new["after"]["research"] == 16 and new["after"]["pretrain"] == 16

    for name, s in (("before", before), ("after", after)):
        txt = "\n".join(f"{jid:4s} {s['results'][jid]}" for jid in s["order"]) + f"\ntenant_used {s['tenant_used']}\n"
        (out / f"replay_{name}.txt").parent.mkdir(parents=True, exist_ok=True)
        (out / f"replay_{name}.txt").write_text(txt, encoding="utf-8", newline="\n")
    result = {"exercise": "17-M2", "evidence_label": "[SIMULATED]",
              "inputs": {"before": "J01 priority 100 (17-W2 proposal)",
                         "after": "plus J05 in urgent-eval QOS (priority 110)"},
              "before": before, "after": after, "answer": {"new_gpus_by_tenant": new}, "units": {"gpus": "GPUs"}}
    rows = "\n".join(f"| {j} | {before['results'][j]} | {after['results'][j]} |" for j in after["order"])
    md = f"""
# 17-M2 replay: urgent-eval QOS `[SIMULATED]`

| Job | Before (J01 at 100) | After (+ urgent-eval QOS for J05) |
|---|---|---|
{rows}

GPUs placed: {before['gpus_placed']} → {after['gpus_placed']}. New GPUs by tenant: {new}.
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
