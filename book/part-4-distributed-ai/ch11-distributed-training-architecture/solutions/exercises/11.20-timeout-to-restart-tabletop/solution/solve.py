"""11.20 — Rank-to-hardware mapping for the 512-node tabletop.

Usage: python solve.py --out DIR      Evidence label: [MODELED] (assumptions [ILLUSTRATIVE], Table 11.4)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml


def rnd(obj, nd: int = 4):
    """Round floats for deterministic output: 4 significant digits for very large/small, else nd decimals."""
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, float):
        if obj != obj:
            return None
        return float(f"{obj:.{nd}g}") if abs(obj) >= 1e6 or (obj != 0 and abs(obj) < 1e-3) else round(obj, nd)
    if isinstance(obj, dict):
        return {str(k): rnd(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rnd(v, nd) for v in obj]
    return obj


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(rnd(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8")
    print(md)

GPN = 8
EVENTS = {"orionxl-n312": {"gpu": 5, "event": "uncorrectable ECC (Xid 48-class)", "time": "02:58"},
          "orionxl-n141": {"nic": 2, "event": "14 link-down/up events", "time": "01:00"}}
TIMEOUT = "03:12"


def node_ranks(host: str) -> list[int]:
    n = int(host.rsplit("n", 1)[1])
    first = GPN * (n - 1)
    return [first, first + GPN - 1]


def minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def solve() -> dict:
    table = {}
    for host, ev in EVENTS.items():
        lo, hi = node_ranks(host)
        local = ev.get("gpu", ev.get("nic"))
        table[host] = {"node_ranks": [lo, hi], "local_index": local, "global_rank": lo + local, "rail": local,
                       "event": ev["event"], "time": ev["time"]}
    gap = minutes(TIMEOUT) - minutes(EVENTS["orionxl-n312"]["time"])
    return {"inputs": {"nodes": "orionxl-n[001-512]", "gpus_per_node": GPN, "order": "TP fastest"},
            "answer": table,
            "timing": {"ecc_to_timeout_min": gap, "nic_flap_runtime_before_timeout_min": minutes(TIMEOUT) - minutes("01:00")},
            "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    a = r["answer"]
    # Key 11.20: rank 2493 (2488-2495), rank 1122 (1120-1127), rail 2.
    assert a["orionxl-n312"]["global_rank"] == 2493 and a["orionxl-n312"]["node_ranks"] == [2488, 2495]
    assert a["orionxl-n141"]["global_rank"] == 1122 and a["orionxl-n141"]["node_ranks"] == [1120, 1127]
    assert a["orionxl-n141"]["rail"] == 2
    assert r["timing"]["ecc_to_timeout_min"] == 14        # >= one ~10 min watchdog period


def report(r: dict) -> str:
    rows = "\n".join(f"| {h} | {v['node_ranks'][0]}-{v['node_ranks'][1]} | {v['global_rank']} | {v['rail']} | {v['time']} {v['event']} |"
                     for h, v in r["answer"].items())
    return f"""# 11.20 — Rank-to-hardware map `[MODELED]`

| Node | Node ranks | Implicated rank | Rail | Event |
|---|---|---|---|---|
{rows}

ECC event to timeout: {r['timing']['ecc_to_timeout_min']} min; the job ran {r['timing']['nic_flap_runtime_before_timeout_min']} min with the flapping NIC.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r))


if __name__ == "__main__":
    main()
