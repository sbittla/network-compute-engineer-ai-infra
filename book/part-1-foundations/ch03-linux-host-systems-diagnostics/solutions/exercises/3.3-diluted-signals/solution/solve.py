#!/usr/bin/env python3
"""3.3: largest blocked-task count consistent with %iowait on a 224-CPU host.

Usage: python solve.py --out DIR
Inputs from the prompt: 224 CPUs, %iowait 4.5, load average 12, 92 % idle.
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

CPUS, IOWAIT_PCT, LOAD_AVG = 224, 4.5, 12
KEY_MAX_BLOCKED = 10.1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    max_blocked = IOWAIT_PCT / 100 * CPUS
    running_implied = LOAD_AVG - round(max_blocked)
    assert abs(max_blocked - KEY_MAX_BLOCKED) < 0.05
    result = {"evidence": "[MODELED]", "inputs": {"cpus": CPUS, "iowait_pct": IOWAIT_PCT, "load_avg": LOAD_AVG},
              "answer": {"max_blocked_tasks": round(max_blocked, 2), "about": round(max_blocked),
                         "runnable_implied_by_load": running_implied,
                         "next_metrics": ["vmstat 1 5 (column b, drop first row)",
                                          "iostat -x 1 3 (r_await, w_await, aqu-sz, last report)"]},
              "units": "tasks"}
    md = ["# 3.3", "", f"- max blocked = {IOWAIT_PCT / 100} x {CPUS} = {max_blocked:.2f} (about {round(max_blocked)})",
          f"- load average {LOAD_AVG} = ~{round(max_blocked)} D-state + ~{running_implied} runnable"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
