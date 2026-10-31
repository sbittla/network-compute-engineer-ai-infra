"""W2 - power capping in a tighter hall: 30 kW racks, 10 % transient margin, 64 nodes, 16 (then 22) racks.

python solve.py --out DIR.  Cap curve read from the package's lab/data/power_cap_curve.csv [ILLUSTRATIVE];
hall parameters from the prompt. Results [MODELED].
Method (manuscript Section 21.8): node peak = 4.6 kW + 8 × cap; nodes/rack = min(4, floor(budget / peak));
deployable = min(64, racks × nodes/rack); throughput = deployable × relative throughput (node-equivalents).
"""
import argparse
import json
import math
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
RACK_LIMIT_KW = 30.0
MARGIN = 0.10
NODES = 64
RACKS = 16
RACKS_EXPANDED = 22
SLOTS = 4
BASE_KW = 4.6
GPUS_PER_NODE = 8
ASKED_CAPS = (650, 550, 350)
KEY = {650: (2, 31.7), 550: (3, 45.4), 350: (3, 33.6)}      # nodes/rack, throughput (16 racks)
KEY_EXPANDED = {550: 60.5, 650: 43.6, 700: 44.0}
KEY_FOURTH_NODE_CAP_W = 269
TOL = 0.05


def table(curve: pd.DataFrame, racks: int) -> list[dict]:
    budget = RACK_LIMIT_KW * (1 - MARGIN)
    rows = []
    for r in curve.sort_values("gpu_power_cap_w").itertuples():
        peak = BASE_KW + GPUS_PER_NODE * r.gpu_power_cap_w / 1000
        npr = min(SLOTS, int(budget // peak))
        dep = min(NODES, racks * npr)
        rows.append({"cap_w": int(r.gpu_power_cap_w), "node_peak_kw": round(peak, 2), "nodes_per_rack": npr,
                     "deployable_nodes": dep, "rel_throughput": float(r.rel_throughput),
                     "cluster_throughput": round(dep * r.rel_throughput, 2),
                     "racks_for_all_64": math.ceil(NODES / npr) if npr else None,
                     "unused_budget_kw": round(budget - npr * peak, 2)})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    curve = pd.read_csv(DATA / "power_cap_curve.csv")
    budget = RACK_LIMIT_KW * (1 - MARGIN)

    t16 = table(curve, RACKS)
    t22 = table(curve, RACKS_EXPANDED)
    by16 = {r["cap_w"]: r for r in t16}
    by22 = {r["cap_w"]: r for r in t22}
    for cap, (npr, thr) in KEY.items():
        assert by16[cap]["nodes_per_rack"] == npr, cap
        assert abs(by16[cap]["cluster_throughput"] - thr) <= TOL, (cap, by16[cap]["cluster_throughput"])
    best16 = max(t16, key=lambda r: (r["cluster_throughput"], r["cap_w"]))["cap_w"]
    best22 = max(t22, key=lambda r: (r["cluster_throughput"], r["cap_w"]))["cap_w"]
    assert best16 == 550 and best22 == 550
    for cap, thr in KEY_EXPANDED.items():
        assert abs(by22[cap]["cluster_throughput"] - thr) <= TOL, (cap, by22[cap]["cluster_throughput"])
    fourth_cap_w = (budget / 4 - BASE_KW) / GPUS_PER_NODE * 1000
    assert abs(fourth_cap_w - KEY_FOURTH_NODE_CAP_W) <= 0.5
    assert by16[700]["racks_for_all_64"] == 32

    result = {
        "exercise": "W2", "evidence_label": "[MODELED]",
        "inputs": {"rack_limit_kw": RACK_LIMIT_KW, "transient_margin": MARGIN, "nodes": NODES, "racks": RACKS,
                   "racks_expanded": RACKS_EXPANDED, "rack_slots": SLOTS, "node_base_kw": BASE_KW},
        "steps": {"rack_budget_kw": round(budget, 2), "table_16_racks": t16, "table_22_racks": t22,
                  "max_cap_for_fourth_node_w": round(fourth_cap_w, 1)},
        "answer": {"asked_caps_16_racks": {str(c): {"nodes_per_rack": by16[c]["nodes_per_rack"],
                                                    "cluster_throughput": by16[c]["cluster_throughput"]}
                                           for c in ASKED_CAPS},
                   "best_cap_16_racks_w": best16, "best_cap_22_racks_w": best22,
                   "throughput_22_racks_at_550w": by22[550]["cluster_throughput"],
                   "throughput_22_racks_uncapped": by22[700]["cluster_throughput"]},
        "units": {"cluster_throughput": "node-equivalents (uncapped HX8 node = 1.0)", "power": "kW", "cap": "W"},
        "tolerance": TOL,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# W2 - capping in a tighter hall `[MODELED]`", "",
          f"Rack budget = {RACK_LIMIT_KW} × (1 - {MARGIN}) = {budget:.1f} kW; node peak = {BASE_KW} + 8 × cap", "",
          "| Cap (W) | Node peak (kW) | Nodes/rack | Deployable, 16 racks | Throughput, 16 racks | Deployable, 22 racks | Throughput, 22 racks |",
          "|---|---|---|---|---|---|---|"]
    for r in t16:
        r22 = by22[r["cap_w"]]
        md.append(f"| {r['cap_w']} | {r['node_peak_kw']} | {r['nodes_per_rack']} | {r['deployable_nodes']} | "
                  f"{r['cluster_throughput']} | {r22['deployable_nodes']} | {r22['cluster_throughput']} |")
    md += ["", f"Best cap: {best16} W on 16 racks and on 22 racks. A fourth node per rack would need a cap "
               f"<= {fourth_cap_w:.0f} W, below the curve.", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
