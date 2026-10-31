"""T1 - the PDU trip at job start in the legacy hall: currents, single-side budget, and the guardrail cap.

python solve.py --out DIR.  Inputs from the case evidence and the canonical circuit [ILLUSTRATIVE];
results [MODELED].  Method (manuscript Sections 21.6 and 21.8): a 2N rack must fit on ONE side;
planned budget = circuit continuous kW × (1 - transient margin); node peak = 4.6 kW + 8 × cap.
"""
import argparse
import json
import math
from pathlib import Path

VOLTS = 415
PF = 0.95
CIRCUIT_KW = 32.78             # one canonical circuit per side (legacy hall, declared variation)
PDU_TRIP_A = 48                # PDU electronic overcurrent setting (= continuous current of the circuit)
BREAKER_A = 60
MARGIN = 0.10
BASE_KW = 4.6
GPUS_PER_NODE = 8
CURVE_MIN_CAP_W = 350          # lowest cap in lab/data/power_cap_curve.csv (rel. throughput 0.70)
OBSERVED_KW = {"lh-03 idle 08:55": 12.1, "lh-03 job start 09:02:10": 41.6, "lh-04 peak (3 nodes)": 30.9}
PLANNED_CLAIM_KW = 41.0        # capacity plan: "41 kW max <= 2 × 32.78 kW"
KEY = {"budget_kw": 29.5, "cap_for_four_w": 347, "three_at_650_kw": 29.4, "job_start_amps": 61}
TOL = 0.5


def amps(kw: float) -> float:
    return kw * 1000 / (math.sqrt(3) * VOLTS * PF)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    budget = CIRCUIT_KW * (1 - MARGIN)
    circuit_amps = amps(CIRCUIT_KW)
    observed_amps = {k: round(amps(v), 1) for k, v in OBSERVED_KW.items()}
    four_uncapped = 4 * (BASE_KW + GPUS_PER_NODE * 0.700)
    cap_for_four_w = (budget / 4 - BASE_KW) / GPUS_PER_NODE * 1000
    four_at_min_cap = 4 * (BASE_KW + GPUS_PER_NODE * CURVE_MIN_CAP_W / 1000)
    three_at_650 = 3 * (BASE_KW + GPUS_PER_NODE * 0.650)
    both_sides_claim = 2 * CIRCUIT_KW

    assert abs(budget - KEY["budget_kw"]) <= 0.05
    assert abs(cap_for_four_w - KEY["cap_for_four_w"]) <= TOL
    assert abs(three_at_650 - KEY["three_at_650_kw"]) <= 0.05 and three_at_650 <= budget
    assert abs(amps(OBSERVED_KW["lh-03 job start 09:02:10"]) - KEY["job_start_amps"]) <= 1.0
    assert amps(OBSERVED_KW["lh-03 job start 09:02:10"]) > PDU_TRIP_A > amps(OBSERVED_KW["lh-04 peak (3 nodes)"])
    assert four_at_min_cap > budget            # even the lowest cap on the curve does not fit four nodes
    assert cap_for_four_w < CURVE_MIN_CAP_W

    result = {
        "exercise": "T1", "evidence_label": "[MODELED]",
        "inputs": {"circuit_kw": CIRCUIT_KW, "volts": VOLTS, "power_factor": PF, "pdu_trip_a": PDU_TRIP_A,
                   "breaker_a": BREAKER_A, "transient_margin": MARGIN, "node_base_kw": BASE_KW,
                   "observed_kw": OBSERVED_KW, "planned_claim_kw": PLANNED_CLAIM_KW},
        "steps": {"circuit_continuous_amps": round(circuit_amps, 1), "observed_amps": observed_amps,
                  "four_uncapped_nodes_kw": round(four_uncapped, 1), "plan_assumed_both_sides_kw": round(both_sides_claim, 2),
                  "four_nodes_at_350w_kw": round(four_at_min_cap, 1)},
        "answer": {"single_side_budget_kw": round(budget, 1), "max_cap_for_four_nodes_w": round(cap_for_four_w),
                   "guardrail": "3 nodes per legacy rack at <= 650 W",
                   "three_nodes_at_650w_kw": round(three_at_650, 1)},
        "units": {"power": "kW", "current": "A per phase", "cap": "W per GPU"},
        "tolerance": TOL,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# T1 - the breaker that tripped at job start `[MODELED]`", "",
          f"- Circuit: {CIRCUIT_KW} kW continuous = {circuit_amps:.1f} A per phase at {VOLTS} V, PF {PF}",
          f"- Plan claimed {PLANNED_CLAIM_KW} kW <= 2 × {CIRCUIT_KW} = {both_sides_claim:.2f} kW (wrong: 2N means one side)"]
    md += [f"- {k}: {OBSERVED_KW[k]} kW = {v} A" for k, v in observed_amps.items()]
    md += [f"- Single-side budget = {CIRCUIT_KW} × (1 - {MARGIN}) = **{budget:.1f} kW**",
           f"- Four nodes: <= {budget / 4:.3f} kW each -> cap <= ({budget / 4:.3f} - {BASE_KW}) / 8 = "
           f"**{cap_for_four_w:.0f} W** (below the curve; at 350 W four nodes still need {four_at_min_cap:.1f} kW)",
           f"- Guardrail: **3 nodes at <= 650 W** = {three_at_650:.1f} kW <= {budget:.1f} kW", ""]
    (out / "result.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
