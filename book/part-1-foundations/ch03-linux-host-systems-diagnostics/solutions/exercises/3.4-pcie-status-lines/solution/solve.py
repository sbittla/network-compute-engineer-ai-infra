#!/usr/bin/env python3
"""3.4: apply the capability-vs-status rules to four PCIe lines.

Usage: python solve.py --out DIR
Lines from the prompt; idle threshold (gpu_idle_util_pct) from lab/data/orion_hx8_baseline.yaml.
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

import yaml

BASELINE = Path(__file__).resolve().parents[4] / "lab" / "data" / "orion_hx8_baseline.yaml"
LINES = {  # device, cap (GT/s, width), status (GT/s, width), utilization % or None, under load
    "a": ("gpu", (32, 16), (32, 8), 95, True),
    "b": ("gpu", (32, 16), (2.5, 16), 0, False),
    "c": ("vga", (5, 1), (5, 1), None, False),
    "d": ("nic", (32, 16), (16, 16), None, True),
}
KEY = {"a": "fault-critical", "b": "probably-benign-verify", "c": "healthy", "d": "fault-warning"}
PCIE_EFF = 0.82


def raw_gbps(gts: float, width: int) -> float:
    enc = 128 / 130 if gts >= 8 else 8 / 10
    return gts * width * enc / 8


def classify(dev: str, cap: tuple, sta: tuple, util, loaded: bool, idle_pct: float) -> str:
    if sta[1] < cap[1]:
        return "fault-critical"
    if sta[0] < cap[0]:
        if dev == "gpu" and util is not None and util <= idle_pct:
            return "probably-benign-verify"
        return "fault-warning"
    return "healthy"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    idle = yaml.safe_load(BASELINE.read_text(encoding="utf-8"))["thresholds"]["gpu_idle_util_pct"]
    ans = {}
    for k, (dev, cap, sta, util, loaded) in LINES.items():
        v = classify(dev, cap, sta, util, loaded, idle)
        assert v == KEY[k], (k, v)
        ans[k] = {"verdict": v, "cap_raw_GBps": round(raw_gbps(*cap), 2), "status_raw_GBps": round(raw_gbps(*sta), 2)}
    d_ach = PCIE_EFF * raw_gbps(16, 16)
    assert abs(raw_gbps(16, 16) - 31.5) < 0.01 and abs(d_ach - 25.8) < 0.05 and d_ach < 50
    ans["d"]["achievable_GBps"] = round(d_ach, 2)
    ans["d"]["nic_line_rate_GBps"] = 50.0
    result = {"evidence": "[MODELED]", "answer": ans, "units": "GB/s per direction"}
    md = ["# 3.4", ""] + [f"- ({k}) {v['verdict']}: status {v['status_raw_GBps']} of {v['cap_raw_GBps']} GB/s raw"
                          for k, v in ans.items()]
    md.append(f"- (d) achievable {d_ach:.1f} GB/s < 50 GB/s line rate: rail PCIe-capped")
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
