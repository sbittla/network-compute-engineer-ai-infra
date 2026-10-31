"""W1 — PFC headroom per port per lossless priority, and for a whole 64-port spine, at 400 and 800 Gb/s.

Usage: python solve.py --out DIR

H = 2 x MTU + 2 x r x (L / v) + r x t_resp + 64 B (manuscript Section 9.4). Chapter conventions:
port MTU 9,216 B; v = 2e8 m/s (5 ns/m); t_resp = 1 us; prompt: 150 m cables, 64 ports, 2 lossless
priorities. [MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MTU_B, NS_PER_M, T_RESP_NS, PFC_B = 9216, 5, 1000, 64
L_M, PORTS, PRIORITIES = 150, 64, 2
KEY = {"a_b": 143_496, "b_b": 18_367_488, "c_b": 268_496, "c_ratio": 1.87}


def headroom(rate_gbps: float, length_m: float) -> dict:
    r = rate_gbps / 8                       # B/ns
    terms = {"two_mtu": 2 * MTU_B, "wire": 2 * r * length_m * NS_PER_M, "response": r * T_RESP_NS, "pfc": PFC_B}
    return {"terms_b": {k: round(v) for k, v in terms.items()}, "total_b": round(sum(terms.values()))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    a = headroom(400, L_M)
    b = PORTS * PRIORITIES * a["total_b"]
    c = headroom(800, L_M)
    ratio = c["total_b"] / a["total_b"]

    assert a["total_b"] == KEY["a_b"] and b == KEY["b_b"] and c["total_b"] == KEY["c_b"]  # exact bytes
    assert abs(ratio - KEY["c_ratio"]) < 0.005

    result = {"exercise": "W1", "evidence_label": "[MODELED]",
              "inputs": {"mtu_b": MTU_B, "ns_per_m": NS_PER_M, "t_resp_ns": T_RESP_NS, "cable_m": L_M,
                         "ports": PORTS, "lossless_priorities": PRIORITIES},
              "steps": {"one_way_delay_ns": L_M * NS_PER_M, "a_terms_b": a["terms_b"], "c_terms_b": c["terms_b"]},
              "answer": {"a_headroom_per_port_priority_b": a["total_b"], "b_switch_total_b": b,
                         "c_headroom_800g_b": c["total_b"], "c_ratio_800_over_400": round(ratio, 3)},
              "units": "bytes", "tolerance": "exact bytes; ratio ±0.005"}
    t = a["terms_b"]
    u = c["terms_b"]
    md = f"""# W1 — result `[MODELED]`

- L / v = {L_M} m × 5 ns/m = {L_M * NS_PER_M} ns
- (a) 400 Gb/s: {t['two_mtu']:,} + {t['wire']:,} + {t['response']:,} + {t['pfc']} = **{a['total_b']:,} B** per port per lossless priority
- (b) {PORTS} × {PRIORITIES} × {a['total_b']:,} = **{b:,} B ≈ {b / 1e6:.1f} MB**
- (c) 800 Gb/s: {u['two_mtu']:,} + {u['wire']:,} + {u['response']:,} + {u['pfc']} = **{c['total_b']:,} B** ({ratio:.2f}× the 400 Gb/s value)
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("W1 ok")


if __name__ == "__main__":
    main()
