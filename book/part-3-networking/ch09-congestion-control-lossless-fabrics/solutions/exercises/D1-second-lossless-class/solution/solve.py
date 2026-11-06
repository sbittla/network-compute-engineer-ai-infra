"""D1 — Extra headroom a second lossless priority costs on a rail leaf and on a spine.

Usage: python solve.py --out DIR

Prompt: rail leaf = 32 host ports at 50 m + 32 spine ports at 100 m; spine = 64 ports at 100 m (ORION
leaf-spine runs). H per (port, priority) from manuscript Section 9.4 / Table 9.3. [MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MTU_B, NS_PER_M, T_RESP_NS, PFC_B, R_B_PER_NS = 9216, 5, 1000, 64, 50
LEAF_PORTS = {50: 32, 100: 32}
SPINE_PORTS = {100: 64}
KEY = {"h50": 93_496, "h100": 118_496, "leaf": 6_783_744, "spine": 7_583_744}


def headroom(length_m: float) -> int:
    return round(2 * MTU_B + 2 * R_B_PER_NS * length_m * NS_PER_M + R_B_PER_NS * T_RESP_NS + PFC_B)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    h = {L: headroom(L) for L in (50, 100)}
    leaf = sum(n * h[L] for L, n in LEAF_PORTS.items())
    spine = sum(n * h[L] for L, n in SPINE_PORTS.items())
    assert h[50] == KEY["h50"] and h[100] == KEY["h100"] and leaf == KEY["leaf"] and spine == KEY["spine"]

    result = {"exercise": "D1", "evidence_label": "[MODELED]",
              "inputs": {"leaf_ports_by_length_m": LEAF_PORTS, "spine_ports_by_length_m": SPINE_PORTS,
                         "mtu_b": MTU_B, "t_resp_ns": T_RESP_NS},
              "steps": {"headroom_per_port_priority_b": h},
              "answer": {"extra_headroom_per_rail_leaf_b": leaf, "extra_headroom_per_spine_b": spine,
                         "two_lossless_priorities_per_rail_leaf_b": 2 * leaf},
              "units": "bytes", "tolerance": "exact"}
    md = f"""# D1 — result `[MODELED]`

- H(50 m) = {h[50]:,} B; H(100 m) = {h[100]:,} B per port per lossless priority
- Rail leaf, one more lossless priority: 32 × {h[50]:,} + 32 × {h[100]:,} = **{leaf:,} B ≈ {leaf / 1e6:.1f} MB**
- Spine, one more lossless priority: 64 × {h[100]:,} = **{spine:,} B ≈ {spine / 1e6:.1f} MB**
- Rail leaf with two lossless priorities in total: {2 * leaf:,} B ≈ {2 * leaf / 1e6:.1f} MB
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("D1 ok")


if __name__ == "__main__":
    main()
