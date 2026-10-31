"""17-W2 — Replay the Monday queue with J01 raised to priority 100 (Chapter 17).

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
    base = summarize(sim.schedule(cluster, jobs))
    variant_jobs = [dict(j, priority=100) if j["job_id"] == "J01" else dict(j) for j in jobs]
    var = summarize(sim.schedule(cluster, variant_jobs))

    def new_by_tenant(s: dict) -> dict:
        start = sim.build_state(cluster)["tenants"]
        return {t: s["tenant_used"][t] - start[t]["used"] for t in sorted(start)}

    # Baseline = Table 17.7; variant = answer key 17-W2
    assert base["order"][:3] == ["J10", "J05", "J12"] and base["results"]["J01"] == "InsufficientCapacity"
    assert var["order"][:3] == ["J10", "J01", "J05"]
    assert var["results"]["J01"] == ["orion-n13", "orion-n18", "orion-n22", "orion-n24"]
    assert var["results"]["J05"] == "InsufficientCapacity" and var["results"]["J08"] == "InsufficientCapacity"
    unchanged = [j for j in base["results"] if j not in ("J01", "J05", "J08")]
    assert all(base["results"][j] == var["results"][j] for j in unchanged)
    assert base["gpus_placed"] == var["gpus_placed"] == 69
    nb, nv = new_by_tenant(base), new_by_tenant(var)
    assert nb == {"finetune": 14, "inference": 15, "pretrain": 16, "research": 16, "search": 8}, nb
    assert nv == {"finetune": 14, "inference": 15, "pretrain": 32, "research": 0, "search": 8}, nv
    assert var["tenant_used"]["pretrain"] == 128 and var["tenant_used"]["research"] == 18

    result = {"exercise": "17-W2", "evidence_label": "[SIMULATED]",
              "inputs": {"change": "J01 priority 50 -> 100", "data": "lab/data (seed 17)"},
              "baseline": base, "variant": var,
              "answer": {"gpus_placed": {"baseline": base["gpus_placed"], "variant": var["gpus_placed"]},
                         "new_gpus_by_tenant": {"baseline": nb, "variant": nv}},
              "units": {"gpus": "GPUs"}}
    (out / "job_queue_j01_p100.json").parent.mkdir(parents=True, exist_ok=True)
    (out / "job_queue_j01_p100.json").write_text(json.dumps(variant_jobs, indent=1, sort_keys=True) + "\n",
                                                 encoding="utf-8", newline="\n")
    lines = [f"{jid:4s} {var['results'][jid]}" for jid in var["order"]]
    (out / "simulator_output.txt").write_text("\n".join(lines) + f"\ntenant_used {var['tenant_used']}\n",
                                              encoding="utf-8", newline="\n")
    rows = "\n".join(f"| {j} | {base['results'][j]} | {var['results'][j]} |" for j in var["order"])
    md = f"""
# 17-W2 replay `[SIMULATED]`

| Job (variant order) | Baseline | J01 at priority 100 |
|---|---|---|
{rows}

GPUs placed: baseline {base['gpus_placed']}, variant {var['gpus_placed']}.
New GPUs by tenant: baseline {nb}; variant {nv}.
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
