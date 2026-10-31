#!/usr/bin/env python3
"""2.1.3: usable capacity of a 2N rack, 2 x 60 A 415 V three-phase circuits per side.

Usage: python solve.py --out DIR
Electrical constants from the package's lab/data/facility_envelope.yaml.
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

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"
AMPS = 60
CIRCUITS_PER_SIDE = 2
KEY = {"kva": 43.13, "kw_circuit": 32.78, "kw_side": 65.55}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    el = yaml.safe_load((DATA / "facility_envelope.yaml").read_text(encoding="utf-8"))["electrical"]
    kva = math.sqrt(3) * el["circuit_voltage_v"] * AMPS / 1e3
    kw_c = kva * el["continuous_load_derate"] * el["power_factor"]
    kw_side = CIRCUITS_PER_SIDE * kw_c
    for name, got in (("kva", kva), ("kw_circuit", kw_c), ("kw_side", kw_side)):
        assert abs(got - KEY[name]) < 0.01, (name, got)
    ans = {"kva_per_circuit": round(kva, 3), "kw_per_circuit": round(kw_c, 3), "kw_per_side": round(kw_side, 3),
           "rack_usable_kw_2n": round(kw_side, 3), "wrong_sum_of_sides_kw": round(2 * kw_side, 3)}
    result = {"evidence": "[MODELED]", "inputs": {**el, "amps": AMPS, "circuits_per_side": CIRCUITS_PER_SIDE},
              "answer": ans, "units": {"power": "kW", "apparent_power": "kVA"}}
    md = ["# 2.1.3", "", f"- sqrt(3) x {el['circuit_voltage_v']} V x {AMPS} A = {kva:.2f} kVA",
          f"- x {el['continuous_load_derate']} x {el['power_factor']} = {kw_c:.2f} kW per circuit",
          f"- 2 circuits = {kw_side:.2f} kW per side = usable rack capacity under 2N (not {2 * kw_side:.1f} kW)"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
