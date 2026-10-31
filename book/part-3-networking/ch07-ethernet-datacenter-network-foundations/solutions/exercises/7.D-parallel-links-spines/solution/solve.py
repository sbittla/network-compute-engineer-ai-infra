"""7.D — Compare 4 spines x 8 links (A), 8 spines x 4 links (B) and 4 spines x 8-member LAG (C) for ORION-256.

Usage: python solve.py --out DIR

Capacities come from the reference fabric_capacity (solutions/lab/fabric_lab.py). For C, BGP sees one
path per spine and still splits traffic 4 ways, so a failed LAG member behaves like a failed link in A
(no link-bandwidth/UCMP assumed). 8 rail leaves, 400 Gb/s links, 64-port spines. [MODELED]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lab"))
import fabric_lab  # noqa: E402

LEAVES, GBPS, SPINE_RADIX = 8, 400, 64
OPTIONS = {"A": {"spines": 4, "links": 8, "lag": False},
           "B": {"spines": 8, "links": 4, "lag": False},
           "C": {"spines": 4, "links": 8, "lag": True}}
KEY = {  # solutions/exercises-key.md 7.D (Tb/s and counts)
    "A": {"ingress_link_down": 11.2, "ingress_spine_down": 9.6, "bisection_spine_down": 38.4, "ebgp": 256, "bfd": 256, "ecmp_width": 32, "spine_ports_used": 64},
    "B": {"ingress_link_down": 9.6, "ingress_spine_down": 11.2, "bisection_spine_down": 44.8, "ebgp": 256, "bfd": 256, "ecmp_width": 32, "spine_ports_used": 32},
    "C": {"ingress_link_down": 11.2, "ingress_spine_down": 9.6, "bisection_spine_down": 38.4, "ebgp": 32, "bfd": 32, "ecmp_width": 4, "spine_ports_used": 64},
}


def capacity(spines: int, links: int, fail: str | None) -> dict:
    counts = [[links] * spines for _ in range(LEAVES)]
    if fail == "link":
        counts[0][0] -= 1
    elif fail == "spine":
        for row in counts:
            row[0] = 0
    r = fabric_lab.fabric_capacity(counts, GBPS)
    return {"ingress_tbps": r["ecmp_ingress_gbps"][0] / 1000, "bisection_tbps": r["bisection_gbps"] / 1000}


def evaluate(name: str, o: dict) -> dict:
    s, k = o["spines"], o["links"]
    base = capacity(s, k, None)
    link = capacity(s, k, "link")
    spine = capacity(s, k, "spine")
    sessions = LEAVES * s if o["lag"] else LEAVES * s * k
    return {
        "spines": s, "links_per_pair": k, "baseline_bisection_tbps": base["bisection_tbps"],
        "ingress_link_down": link["ingress_tbps"], "ingress_link_down_pct": round(100 * (1 - link["ingress_tbps"] / base["ingress_tbps"]), 2),
        "ingress_spine_down": spine["ingress_tbps"], "ingress_spine_down_pct": round(100 * (1 - spine["ingress_tbps"] / base["ingress_tbps"]), 2),
        "bisection_spine_down": spine["bisection_tbps"],
        "ebgp": sessions, "bfd": sessions, "micro_bfd_members": LEAVES * s * k if o["lag"] else 0,
        "spine_ports_used": LEAVES * k, "spine_ports_idle": SPINE_RADIX - LEAVES * k, "total_spine_ports": s * LEAVES * k,
        "ecmp_width": s if o["lag"] else s * k,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    table = {n: evaluate(n, o) for n, o in OPTIONS.items()}
    for n, exp in KEY.items():
        for f, v in exp.items():
            assert abs(table[n][f] - v) < 1e-9, (n, f, table[n][f], v)
    assert all(abs(t["baseline_bisection_tbps"] - 51.2) < 1e-9 for t in table.values())

    result = {"exercise": "7.D", "evidence_label": "[MODELED]",
              "inputs": {"leaves": LEAVES, "link_gbps": GBPS, "spine_radix": SPINE_RADIX, "options": OPTIONS},
              "answer": {n: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in t.items()} for n, t in table.items()},
              "recommendation": "A (or C) for an optics-failure-dominated risk; B if spine drains/faults dominate",
              "units": "Tb/s one direction; session and port counts", "tolerance": "1e-9"}
    lines = ["| Metric | A | B | C |", "|---|---|---|---|"]
    for f in ("ingress_link_down", "ingress_spine_down", "bisection_spine_down", "ebgp", "bfd",
              "micro_bfd_members", "spine_ports_used", "total_spine_ports", "ecmp_width"):
        lines.append(f"| {f} | " + " | ".join(str(round(table[n][f], 3)) for n in "ABC") + " |")
    md = "# 7.D — result `[MODELED]`\n\nCapacities in Tb/s (one direction), ORION-256, 400 Gb/s links.\n\n" + "\n".join(lines) + "\n"
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("7.D ok")


if __name__ == "__main__":
    main()
