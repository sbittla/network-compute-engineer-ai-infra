"""K5 - facility power of ORION-256 at PUE 1.25 (canonical) and 1.45 (declared hot-season variation).

python solve.py --out DIR.  Inputs from the prompt and docs/REFERENCE_CLUSTER.md [ILLUSTRATIVE]; results [MODELED].
Method (manuscript Section 21.4): IT = nodes × sustained kW × (1 + overhead); facility = IT × PUE.
"""
import argparse
import json
from pathlib import Path

NODES = 32                     # ORION-256
SUSTAINED_KW_PER_NODE = 8.5    # Reference Cluster: sustained training node power
OVERHEAD = 0.12                # network/storage/management allowance (lab assumptions.yaml)
PUE_CANON = 1.25               # Reference Cluster canonical PUE
PUE_HOT = 1.45                 # prompt: hot-season variation
KEY = {"it_kw": 304.6, "facility_kw_1_25": 380.8, "facility_kw_1_45": 441.7, "increase_pct": 16.0}
TOL = 0.1                      # kW (and percentage points)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    it_kw = NODES * SUSTAINED_KW_PER_NODE * (1 + OVERHEAD)
    f125 = it_kw * PUE_CANON
    f145 = it_kw * PUE_HOT
    inc = (f145 / f125 - 1) * 100
    non_it = {"pue_1_25": f125 - it_kw, "pue_1_45": f145 - it_kw}
    got = {"it_kw": it_kw, "facility_kw_1_25": f125, "facility_kw_1_45": f145, "increase_pct": inc}
    for k, v in got.items():
        assert abs(v - KEY[k]) <= TOL, (k, v)

    result = {
        "exercise": "K5", "evidence_label": "[MODELED]",
        "inputs": {"nodes": NODES, "sustained_kw_per_node": SUSTAINED_KW_PER_NODE, "overhead": OVERHEAD,
                   "pue_canonical": PUE_CANON, "pue_hot_season_variation": PUE_HOT},
        "steps": {"it_kw": round(it_kw, 2), "non_it_kw": {k: round(v, 1) for k, v in non_it.items()}},
        "answer": {"facility_kw_pue_1_25": round(f125, 1), "facility_kw_pue_1_45": round(f145, 1),
                   "increase_pct": round(inc, 1)},
        "units": {"facility_kw": "kW", "increase_pct": "%"}, "tolerance": TOL,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# K5 - PUE `[MODELED]`", "",
        f"IT = {NODES} × {SUSTAINED_KW_PER_NODE} kW × {1 + OVERHEAD:.2f} = {it_kw:.2f} kW", "",
        f"- PUE {PUE_CANON}: {it_kw:.2f} × {PUE_CANON} = **{f125:.1f} kW** (non-IT {non_it['pue_1_25']:.1f} kW)",
        f"- PUE {PUE_HOT}: {it_kw:.2f} × {PUE_HOT} = **{f145:.1f} kW** (non-IT {non_it['pue_1_45']:.1f} kW)", "",
        f"Increase: {inc:.1f} % more facility power for the same IT work.", "",
    ]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
