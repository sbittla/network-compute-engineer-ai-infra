"""7.W2 — Failure capacity of the 7.W1(a) ORION-384 design and ECMP collision odds for 4 flows on 4 links.

Usage: python solve.py --out DIR

(a) uses the reference fabric_capacity (solutions/lab/fabric_lab.py) on 16 leaves x 8 spines x 4
links at 400 Gb/s and checks it against the hand formulas. (c) is exact combinatorics, confirmed by
enumerating all 4**4 hash outcomes. [MODELED]
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lab"))
import fabric_lab  # noqa: E402

LEAVES, SPINES, LINKS, GBPS = 16, 8, 4, 400
ORION256_LINK_PENALTY_PCT = 12.5   # Table 7.8: 4 x 7 x 0.4 = 11.2 of 12.8 Tb/s
KEY_TBPS = {  # solutions/exercises-key.md 7.W2 (raw uplink, ECMP-aware ingress, bisection)
    "baseline": (12.8, 12.8, 102.4), "link_down": (12.4, 9.6, 102.0), "spine_down": (11.2, 11.2, 89.6),
}


def scenario(name: str) -> dict:
    counts = [[LINKS] * SPINES for _ in range(LEAVES)]
    if name == "link_down":
        counts[0][0] -= 1
    elif name == "spine_down":
        for row in counts:
            row[0] = 0
    r = fabric_lab.fabric_capacity(counts, GBPS)
    return {"raw_uplink_tbps": r["uplink_gbps"][0] / 1000, "ecmp_ingress_tbps": r["ecmp_ingress_gbps"][0] / 1000,
            "bisection_tbps": r["bisection_gbps"] / 1000}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    table = {n: scenario(n) for n in KEY_TBPS}
    hand = {  # hand arithmetic for the ingress column
        "baseline": SPINES * LINKS * GBPS / 1000,
        "link_down": SPINES * (LINKS - 1) * GBPS / 1000,
        "spine_down": (SPINES - 1) * LINKS * GBPS / 1000,
    }
    for n, (raw, ing, bis) in KEY_TBPS.items():
        t = table[n]
        assert abs(t["raw_uplink_tbps"] - raw) < 1e-9 and abs(t["ecmp_ingress_tbps"] - ing) < 1e-9, (n, t)
        assert abs(t["bisection_tbps"] - bis) < 1e-9 and abs(hand[n] - ing) < 1e-9, (n, t)

    base = table["baseline"]["ecmp_ingress_tbps"]
    link_pen = 100 * (base - table["link_down"]["ecmp_ingress_tbps"]) / base
    spine_pen = 100 * (base - table["spine_down"]["ecmp_ingress_tbps"]) / base
    assert abs(link_pen - 25.0) < 1e-9 and abs(spine_pen - 12.5) < 1e-9

    # (c) four flows, four links, uniform independent hashing
    n = 4
    p_formula = math.factorial(n) / n ** n
    e_formula = n * (1 - ((n - 1) / n) ** n)
    outcomes = list(itertools.product(range(n), repeat=n))
    p_enum = sum(len(set(o)) == n for o in outcomes) / len(outcomes)
    e_enum = sum(len(set(o)) for o in outcomes) / len(outcomes)
    assert abs(p_formula - p_enum) < 1e-12 and abs(e_formula - e_enum) < 1e-12
    assert abs(p_formula - 0.094) < 0.0005 and abs(e_formula - 2.73) < 0.005   # key: 9.4 %, 2.73

    result = {
        "exercise": "7.W2", "evidence_label": "[MODELED]",
        "inputs": {"leaves": LEAVES, "spines": SPINES, "links_per_pair": LINKS, "link_gbps": GBPS},
        "steps": {"hand_ingress_tbps": hand, "orion256_link_penalty_pct": ORION256_LINK_PENALTY_PCT,
                  "enumerated_outcomes": len(outcomes)},
        "answer": {"a_table_tbps": {k: {m: round(v, 3) for m, v in t.items()} for k, t in table.items()},
                   "b_link_penalty_pct": round(link_pen, 2), "b_spine_penalty_pct": round(spine_pen, 2),
                   "c_p_no_collision": round(p_formula, 4), "c_expected_links_used": round(e_formula, 4)},
        "units": "Tb/s one direction; probability; links", "tolerance": "1e-9 Tb/s; key rounding for (c)",
    }
    rows = "\n".join(f"| {k} | {t['raw_uplink_tbps']:.1f} | {t['ecmp_ingress_tbps']:.1f} | {t['bisection_tbps']:.1f} |"
                     for k, t in table.items())
    md = f"""# 7.W2 — result `[MODELED]`

| Scenario | Raw uplink (Tb/s) | ECMP-aware ingress (Tb/s) | Bisection (Tb/s) |
|---|---|---|---|
{rows}

- Single-link penalty {link_pen:.1f} % (ORION-256: {ORION256_LINK_PENALTY_PCT} %); single-spine penalty {spine_pen:.1f} % (ORION-256: 25 %)
- P(no collision) = 4!/4⁴ = 24/256 = **{100 * p_formula:.1f} %**; E[links used] = 4 × (1 − (3/4)⁴) = **{e_formula:.2f}**
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("7.W2 ok")


if __name__ == "__main__":
    main()
