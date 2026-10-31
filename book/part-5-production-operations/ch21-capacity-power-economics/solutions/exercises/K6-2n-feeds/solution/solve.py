"""K6 - maximum planned rack load under 2N A/B feeds with a 10 % transient margin.

python solve.py --out DIR.  Circuit constants from docs/REFERENCE_CLUSTER.md [ILLUSTRATIVE]; results [MODELED].
Method (manuscript Sections 21.6-21.7): with 2N either side must carry the whole rack, so
planned peak <= (circuits per side × circuit continuous kW) × (1 - transient margin).
"""
import argparse
import json
import math
from pathlib import Path

VOLTS = 415                    # three-phase line-to-line
AMPS = 60                      # breaker rating
PF = 0.95
CONTINUOUS = 0.80              # 80 % continuous-load rule (North American practice)
MARGIN = 0.10                  # prompt: transient margin
NODE_BASE_KW = 4.6             # canonical node power model: 4.6 kW + 8 × GPU cap
GPUS_PER_NODE = 8
NODE_MAX_KW = NODE_BASE_KW + GPUS_PER_NODE * 0.700   # 10.2 kW uncapped
KEY = {"canonical": 59.0, "legacy": 29.5}
TOL = 0.05                     # kW


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    circuit_kw = math.sqrt(3) * VOLTS * AMPS * PF * CONTINUOUS / 1000
    rows = {}
    for name, circuits in (("canonical", 2), ("legacy", 1)):
        side = circuits * circuit_kw
        planned = side * (1 - MARGIN)
        n = int(planned // NODE_MAX_KW)
        rows[name] = {"circuits_per_side": circuits, "side_continuous_kw": round(side, 2),
                      "planned_peak_kw": round(planned, 1), "uncapped_hx8_nodes_that_fit": min(n, 4),
                      "uncapped_load_kw": round(min(n, 4) * NODE_MAX_KW, 1)}
        assert abs(planned - KEY[name]) <= TOL, (name, planned)
    legacy = circuit_kw * (1 - MARGIN)
    cap_for_three_w = (legacy / 3 - NODE_BASE_KW) / GPUS_PER_NODE * 1000
    three_at_650 = 3 * (NODE_BASE_KW + GPUS_PER_NODE * 0.650)
    assert rows["canonical"]["uncapped_hx8_nodes_that_fit"] == 4
    assert rows["legacy"]["uncapped_hx8_nodes_that_fit"] == 2
    assert three_at_650 <= legacy and abs(three_at_650 - 29.4) <= TOL

    result = {
        "exercise": "K6", "evidence_label": "[MODELED]",
        "inputs": {"volts": VOLTS, "amps": AMPS, "power_factor": PF, "continuous_fraction": CONTINUOUS,
                   "transient_margin": MARGIN, "node_max_kw": NODE_MAX_KW},
        "steps": {"circuit_continuous_kw": round(circuit_kw, 2),
                  "legacy_max_gpu_cap_for_3_nodes_w": round(cap_for_three_w),
                  "legacy_3_nodes_at_650w_kw": round(three_at_650, 1)},
        "answer": rows, "units": "kW", "tolerance_kw": TOL,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# K6 - 2N feeds `[MODELED]`", "",
          f"Circuit: sqrt(3) × {VOLTS} V × {AMPS} A × {PF} × {CONTINUOUS} = {circuit_kw:.2f} kW continuous", ""]
    for name, r in rows.items():
        md.append(f"- {name}: {r['circuits_per_side']} circuit(s) per side = {r['side_continuous_kw']} kW; "
                  f"× (1 - {MARGIN}) = **{r['planned_peak_kw']} kW** planned peak; "
                  f"{r['uncapped_hx8_nodes_that_fit']} uncapped HX8 nodes ({r['uncapped_load_kw']} kW)")
    md += ["", f"Legacy rack: three nodes need a GPU cap <= {cap_for_three_w:.0f} W; at 650 W they draw "
               f"{three_at_650:.1f} kW.",
           "Failure scenario: loss of side A or B; the surviving side must carry the whole rack.", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
