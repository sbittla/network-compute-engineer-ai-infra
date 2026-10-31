#!/usr/bin/env python3
"""2.9: Rack-X electrical, transient, heat-removal and floor arithmetic.

Usage: python solve.py --out DIR
All inputs are the prompt's [ILLUSTRATIVE] assumptions (named constants below).
"""
from __future__ import annotations

import argparse
import json
import re
import math
from pathlib import Path


def house(line: str) -> str:
    """Apply the book's copyedit house style to generated Markdown (x -> ×, ~ -> ≈, '40 %', µs)."""
    line = re.sub(r"(\d)%", r"\1 %", line)
    line = line.replace(" x ", " × ")
    line = re.sub(r"(\d)x\b", r"\1×", line)
    line = re.sub(r"~ ?", "≈ ", line)
    line = re.sub(r"(\d) us\b", r"\1 µs", line)
    return line.replace("scaleout", "scale-out").replace("scaleup", "scale-up")

IT_KW, MARGIN, VOLTS, DERATE, PF = 120.0, 0.15, 415, 0.80, 0.95
CAPTURE, CP_L, RHO_L, DT_L = 0.85, 3.90, 1.02, 8
CP_A, RHO_A, DT_A = 1.006, 1.20, 15
RACKS_PER_ROW, CDU_KW, STEP_FRACTION = 8, 1000.0, 0.30
RACK_KG, FOOTPRINT_M2, FLOOR_RATING = 1400, 0.6 * 1.2, 1200
M3S_TO_CFM = 2118.88
KEY = {"side_kw": 138.0, "c125_kw": 68.29, "c160_kw": 87.41, "step_kw": 288.0, "lpm_rack": 192.3,
       "lpm_row": 1538.0, "cfm_rack": 2106.0, "cdu_util_one_failed": 0.816, "floor": 1944.0}


def circuit_kw(amps: float) -> float:
    return math.sqrt(3) * VOLTS * amps * DERATE * PF / 1e3


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    side = IT_KW * (1 + MARGIN)
    c125, c160 = circuit_kw(125), circuit_kw(160)
    n125 = math.ceil(side / c125)
    n160 = math.ceil(side / c160)
    step = RACKS_PER_ROW * IT_KW * STEP_FRACTION
    liquid, air = CAPTURE * IT_KW, (1 - CAPTURE) * IT_KW
    lpm = liquid / (CP_L * DT_L) / RHO_L * 60
    cfm = air / (CP_A * RHO_A * DT_A) * M3S_TO_CFM
    row_liquid = RACKS_PER_ROW * liquid
    cdus_n = math.ceil(row_liquid / CDU_KW)
    cdus = cdus_n + 1
    floor = RACK_KG / FOOTPRINT_M2
    ans = {"side_kw": side, "c125_kw": c125, "c125_x2_kw": 2 * c125, "n125": n125, "c125_x3_kw": 3 * c125,
           "c160_kw": c160, "n160": n160, "c160_x2_kw": 2 * c160, "headroom_160_kw": 2 * c160 - side,
           "step_kw": step, "liquid_kw": liquid, "air_kw": air, "lpm_rack": lpm, "lpm_row": RACKS_PER_ROW * lpm,
           "row_liquid_kw": row_liquid, "cfm_rack": cfm, "cdus_n_plus_1": cdus,
           "cdu_util_normal": row_liquid / (cdus * CDU_KW), "cdu_util_one_failed": row_liquid / (cdus_n * CDU_KW),
           "floor": floor, "envelope_side_80pct_kw": 0.8 * 2 * c160, "envelope_min_flow_lpm": 0.85 * lpm}
    for k, v in KEY.items():
        assert abs(ans[k] - v) <= 0.002 * v, (k, ans[k], v)
    assert 2 * c125 < side <= 3 * c125 and n125 == 3 and n160 == 2 and cdus == 2 and floor > FLOOR_RATING
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] assumptions",
              "answer": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in ans.items()},
              "units": {"power": "kW", "flow": "L/min", "air": "CFM", "floor": "kg/m2"}}
    md = ["# 2.9 — Rack-X `[MODELED]`", "", "| Quantity | Value |", "|---|---:|"]
    md += [f"| {k} | {result['answer'][k]} |" for k in ans]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
