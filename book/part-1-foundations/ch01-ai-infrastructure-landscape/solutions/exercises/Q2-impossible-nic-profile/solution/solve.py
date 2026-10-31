#!/usr/bin/env python3
"""Q2: does 40 GB in 0.5 s fit through a 400 Gb/s NIC?

Usage: python solve.py --out DIR
Inputs from the prompt; NIC line rate from docs/REFERENCE_CLUSTER.md.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def house(line: str) -> str:
    """Apply the book's copyedit house style to generated Markdown (x -> ×, ~ -> ≈, '40 %', µs)."""
    line = re.sub(r"(\d)%", r"\1 %", line)
    line = line.replace(" x ", " × ")
    line = re.sub(r"(\d)x\b", r"\1×", line)
    line = re.sub(r"~ ?", "≈ ", line)
    line = re.sub(r"(\d) us\b", r"\1 µs", line)
    return line.replace("scaleout", "scale-out").replace("scaleup", "scale-up")

BYTES_GB = 40.0
WINDOW_S = 0.5
NIC_GBITS = 400
KEY_RATE = 80.0       # GB/s, exercises-key.md Quick self-check Q2


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    rate = BYTES_GB / WINDOW_S
    line = NIC_GBITS / 8
    bound = BYTES_GB / line
    frac = bound / WINDOW_S
    verdict = "IMPOSSIBLE" if frac > 1.0 else "possible"
    assert abs(rate - KEY_RATE) < 1e-9 and line == 50.0 and verdict == "IMPOSSIBLE"
    result = {"evidence": "[MODELED]", "inputs": {"bytes_GB": BYTES_GB, "window_s": WINDOW_S, "nic_Gbps": NIC_GBITS},
              "answer": {"implied_GBps": rate, "line_rate_GBps": line, "lower_bound_s": bound,
                         "ceiling_fraction": round(frac, 3), "verdict": verdict},
              "units": {"rate": "GB/s", "time": "s"}}
    md = ["# Q2", "", f"- implied {rate:.0f} GB/s vs line rate {line:.0f} GB/s",
          f"- lower bound {bound:.2f} s > {WINDOW_S} s observed; ceiling fraction {frac:.2f}: {verdict}"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
