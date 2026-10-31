"""T1 — Headroom provided by a 5 m buffer profile versus what each of orion-be-leaf-r5's ports needs.

Usage: python solve.py --out DIR

H = 2 x MTU + 2 x r x (L / v) + r x t_resp + 64 B; port MTU 9,216 B, t_resp = 1 us, v = 5 ns/m,
r = 400 Gb/s = 50 B/ns (manuscript Section 9.4; prompt). Cable lengths from the T1 evidence table.
[MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MTU_B, NS_PER_M, T_RESP_NS, PFC_B, R_B_PER_NS = 9216, 5, 1000, 64, 50
PROFILE_M = 5
PORTS = {"eth1/7 (orion-n07, 30 m)": 30, "eth1/33 (spine-1, 20 m)": 20, "eth1/57 (spine-4, 100 m)": 100}
KEY = {"provided": 70_996, "need_100": 118_496, "deficit_100": 47_500, "need_20": 78_496, "deficit_20": 7_500,
       "need_30": 83_496, "deficit_30": 12_500}


def headroom(length_m: float) -> int:
    return round(2 * MTU_B + 2 * R_B_PER_NS * length_m * NS_PER_M + R_B_PER_NS * T_RESP_NS + PFC_B)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    provided = headroom(PROFILE_M)
    per_port = {}
    for name, L in PORTS.items():
        need = headroom(L)
        per_port[name] = {"length_m": L, "needed_b": need, "deficit_b": need - provided,
                          "shortfall_pct": round(100 * (need - provided) / need, 1)}
    p100, p20, p30 = (per_port[k] for k in ("eth1/57 (spine-4, 100 m)", "eth1/33 (spine-1, 20 m)", "eth1/7 (orion-n07, 30 m)"))

    assert provided == KEY["provided"]
    assert (p100["needed_b"], p100["deficit_b"]) == (KEY["need_100"], KEY["deficit_100"])
    assert (p20["needed_b"], p20["deficit_b"]) == (KEY["need_20"], KEY["deficit_20"])
    assert (p30["needed_b"], p30["deficit_b"]) == (KEY["need_30"], KEY["deficit_30"])
    assert abs(p100["shortfall_pct"] - 40.1) < 0.1     # key: "≈ 40 % short"

    result = {"exercise": "T1", "evidence_label": "[MODELED]",
              "inputs": {"mtu_b": MTU_B, "ns_per_m": NS_PER_M, "t_resp_ns": T_RESP_NS, "rate_b_per_ns": R_B_PER_NS,
                         "profile_cable_m": PROFILE_M},
              "steps": {"provided_terms_b": {"two_mtu": 2 * MTU_B, "wire": 2 * R_B_PER_NS * PROFILE_M * NS_PER_M,
                                             "response": R_B_PER_NS * T_RESP_NS, "pfc": PFC_B}},
              "answer": {"provided_b": provided, "ports": per_port},
              "units": "bytes per port per lossless priority", "tolerance": "exact"}
    rows = "\n".join(f"| {k} | {v['needed_b']:,} | {v['deficit_b']:,} ({v['shortfall_pct']} %) |" for k, v in per_port.items())
    md = f"""# T1 — result `[MODELED]`

Profile (5 m): 18,432 + 2 × 50 × 25 + 50,000 + 64 = **{provided:,} B** provided per port.

| Port | Needed (B) | Deficit vs profile (B) |
|---|---|---|
{rows}
"""
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md, encoding="utf-8", newline="\n")
    print("T1 ok")


if __name__ == "__main__":
    main()
