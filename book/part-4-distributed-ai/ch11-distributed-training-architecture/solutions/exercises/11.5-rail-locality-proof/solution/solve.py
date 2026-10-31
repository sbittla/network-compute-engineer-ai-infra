"""11.5 — Rail of every DP and PP peer of global rank 19 (TP-fastest order).

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

TP, DP, PP, GPUS_PER_NODE = 8, 8, 4, 8
RANK = 19


def coords(r: int) -> dict:
    return {"tp": r % TP, "dp": (r // TP) % DP, "pp": r // (TP * DP)}


def solve() -> dict:
    c = coords(RANK)
    dp_group = [c["tp"] + TP * k + TP * DP * c["pp"] for k in range(DP)]
    pp_group = [c["tp"] + TP * c["dp"] + TP * DP * j for j in range(PP)]
    place = {r: {"node": r // GPUS_PER_NODE, "local_rank": r % GPUS_PER_NODE, "rail": r % GPUS_PER_NODE}
             for r in sorted(set(dp_group + pp_group))}
    return {"inputs": {"tp": TP, "dp": DP, "pp": PP, "rank": RANK}, "coords": c,
            "dp_group": dp_group, "pp_group": pp_group, "placement": place,
            "answer": {"dp_rails": sorted({place[r]["rail"] for r in dp_group}),
                       "pp_rails": sorted({place[r]["rail"] for r in pp_group})},
            "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    # Key 11.5: DP group {3, 11, ..., 59}, all on rail 3; PP peers 19 + 64j also rail 3.
    assert r["coords"] == {"tp": 3, "dp": 2, "pp": 0}
    assert r["dp_group"] == [3, 11, 19, 27, 35, 43, 51, 59]
    assert r["answer"] == {"dp_rails": [3], "pp_rails": [3]}


def report(r: dict) -> str:
    rows = "\n".join(f"| {k} | {v['node']} | {v['local_rank']} | {v['rail']} |" for k, v in r["placement"].items())
    return f"""# 11.5 — Rail locality `[MODELED]`

rank 19 -> {r['coords']}; DP group {r['dp_group']}; PP group {r['pp_group']}

| Global rank | Node | Local rank | Rail |
|---|---|---|---|
{rows}

All DP and PP peers are on rail {r['answer']['dp_rails'][0]}.
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
