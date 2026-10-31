"""7.O2 — Capacity and ECMP-width columns of the ORION-256 failure table (link, spine, leaf failure).

Usage: python solve.py --out DIR

Runs the reference fabric_capacity (solutions/lab/fabric_lab.py) on ORION-256 (8 leaves x 4 spines
x 8 links, 400 Gb/s). ECMP width = uplinks of an unaffected leaf (orion-be-leaf-r7) toward spines
that still reach the destination rail's leaf. [MODELED]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lab"))
import fabric_lab  # noqa: E402

LEAVES, SPINES, LINKS, GBPS = 8, 4, 8, 400
OBSERVER = 7   # orion-be-leaf-r7: unaffected in every scenario
KEY = {  # solutions/exercises-key.md 7.O2 and Table 7.8 (Tb/s)
    "link":  {"affected_raw": 12.4, "affected_ingress": 11.2, "bisection": 50.8, "ecmp_width": 32},
    "spine": {"affected_raw": 9.6, "affected_ingress": 9.6, "bisection": 38.4, "ecmp_width": 24},
    "leaf":  {"affected_raw": 0.0, "affected_ingress": 0.0, "bisection": 38.4, "ecmp_width": 32},
}


def run(scenario: str) -> dict:
    counts = [[LINKS] * SPINES for _ in range(LEAVES)]
    affected, dest = 0, 0
    if scenario == "link":        # one orion-be-leaf-r0 <-> orion-be-spine-1 link
        counts[0][0] -= 1
    elif scenario == "spine":     # orion-be-spine-2
        for row in counts:
            row[1] = 0
    elif scenario == "leaf":      # orion-be-leaf-r3; width measured toward another rail (rail 0)
        counts[3] = [0] * SPINES
        affected = 3
    r = fabric_lab.fabric_capacity(counts, GBPS)
    width = sum(counts[OBSERVER][s] for s in range(SPINES) if counts[dest][s] > 0)
    return {"affected_raw": r["uplink_gbps"][affected] / 1000, "affected_ingress": r["ecmp_ingress_gbps"][affected] / 1000,
            "bisection": r["bisection_gbps"] / 1000, "ecmp_width": width}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    table = {s: run(s) for s in KEY}
    for s, exp in KEY.items():
        for f, v in exp.items():
            assert abs(table[s][f] - v) < 1e-9, (s, f, table[s][f], v)
    bfd_s = 0.3 * 3
    assert abs(bfd_s - 0.9) < 1e-12

    result = {"exercise": "7.O2", "evidence_label": "[MODELED]",
              "inputs": {"leaves": LEAVES, "spines": SPINES, "links_per_pair": LINKS, "link_gbps": GBPS,
                         "observer_leaf": "orion-be-leaf-r7", "bfd": "300 ms x 3", "bgp_timers_s": [3, 9]},
              "steps": {"bfd_detection_s": bfd_s},
              "answer": {s: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in t.items()} for s, t in table.items()},
              "units": "Tb/s one direction; ECMP width in next hops", "tolerance": "1e-9"}
    rows = "\n".join(f"| {s} | {t['affected_raw']:.1f} | {t['affected_ingress']:.1f} | {t['bisection']:.1f} | {t['ecmp_width']} |"
                     for s, t in table.items())
    md = f"""# 7.O2 — result `[MODELED]`

| Failure | Affected leaf raw uplink (Tb/s) | Affected leaf ECMP-aware ingress (Tb/s) | Bisection (Tb/s) | ECMP width at orion-be-leaf-r7 |
|---|---|---|---|---|
{rows}

Link = one orion-be-leaf-r0↔orion-be-spine-1 link; spine = orion-be-spine-2 (affected leaf: any); leaf = orion-be-leaf-r3.
BFD detection 300 ms × 3 = {bfd_s:.1f} s.
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("7.O2 ok")


if __name__ == "__main__":
    main()
