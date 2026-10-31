"""7.K6 — Raw vs ECMP-aware ingress capacity of orion-be-leaf-r0 after one of its 8 links to spine-1 fails.

Usage: python solve.py --out DIR

Hand formulas from manuscript Section 7.9, cross-checked against the reference
`fabric_capacity` (solutions/lab/fabric_lab.py). [MODELED]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lab"))
import fabric_lab  # noqa: E402  (reference implementation, instructor copy)

LEAVES, SPINES, LINKS_PER_PAIR, LINK_GBPS = 8, 4, 8, 400
KEY = {"raw_gbps": 12_400, "raw_drop_pct": 3.1, "ingress_gbps": 11_200, "ingress_drop_pct": 12.5}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    base_raw = SPINES * LINKS_PER_PAIR * LINK_GBPS                      # 32 x 400
    raw = (SPINES * LINKS_PER_PAIR - 1) * LINK_GBPS                     # 31 x 400
    bundles = [LINKS_PER_PAIR - 1] + [LINKS_PER_PAIR] * (SPINES - 1)    # 7, 8, 8, 8
    ingress = SPINES * min(bundles) * LINK_GBPS                         # 4 x 7 x 400
    raw_drop = 100 * (base_raw - raw) / base_raw
    ingress_drop = 100 * (base_raw - ingress) / base_raw

    counts = [[LINKS_PER_PAIR] * SPINES for _ in range(LEAVES)]
    counts[0][0] -= 1
    ref = fabric_lab.fabric_capacity(counts, LINK_GBPS)

    assert raw == KEY["raw_gbps"] and ingress == KEY["ingress_gbps"]
    assert abs(raw_drop - KEY["raw_drop_pct"]) < 0.05 and abs(ingress_drop - KEY["ingress_drop_pct"]) < 1e-9
    assert ref["uplink_gbps"][0] == raw and ref["ecmp_ingress_gbps"][0] == ingress  # hand == tool

    result = {
        "exercise": "7.K6", "evidence_label": "[MODELED]",
        "inputs": {"leaves": LEAVES, "spines": SPINES, "links_per_pair": LINKS_PER_PAIR, "link_gbps": LINK_GBPS,
                   "failed": "one orion-be-leaf-r0 <-> orion-be-spine-1 link"},
        "steps": {"baseline_gbps": base_raw, "bundles_after_failure": bundles,
                  "fabric_capacity_ref": {"uplink_gbps_leaf_r0": ref["uplink_gbps"][0],
                                          "ecmp_ingress_gbps_leaf_r0": ref["ecmp_ingress_gbps"][0],
                                          "bisection_gbps": ref["bisection_gbps"]}},
        "answer": {"raw_uplink_gbps": raw, "raw_drop_pct": round(raw_drop, 2),
                   "ecmp_ingress_gbps": ingress, "ecmp_ingress_drop_pct": round(ingress_drop, 2)},
        "units": "Gb/s, one direction", "tolerance": "exact Gb/s; percentages ±0.05",
    }
    md = f"""# 7.K6 — result `[MODELED]`

- Raw uplink: 31 × 400 = **{raw:,} Gb/s** vs {base_raw:,} → −{raw_drop:.1f} %
- ECMP-aware ingress: 4 spines × min{tuple(bundles)} × 400 = **{ingress:,} Gb/s** → −{ingress_drop:.1f} %
- Reference `fabric_capacity`: uplink {ref['uplink_gbps'][0]:,.0f}, ingress {ref['ecmp_ingress_gbps'][0]:,.0f}, bisection {ref['bisection_gbps']:,.0f} Gb/s
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("7.K6 ok:", raw, ingress)


if __name__ == "__main__":
    main()
