"""DC1 — Weighted re-acceptance time for a tiered return-to-service policy (Chapter 16).

Usage: python solve.py --out DIR
Writes result.json and result.md; asserts the answer key (solutions/exercises-key.md).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8", newline="\n")


def close(value: float, key: float, tol: float, what: str) -> None:
    assert abs(value - key) <= tol, f"{what}: computed {value} vs key {key} (tol {tol})"


# Repair mix from the prompt [ILLUSTRATIVE]; tier durations from the reference policy (hours).
MIX = {"optic/cable": 0.60, "NIC": 0.25, "GPU/baseboard": 0.10, "DIMM/NVMe": 0.05}
TIER_H = {"optic/cable": 0.75, "NIC": 2.5, "GPU/baseboard": 25.4, "DIMM/NVMe": 5.0}
# Full acceptance per node, Section 16.6 Step 3: 31 + 45 + 1,440 + 10 min
FULL_MIN = 31 + 45 + 1440 + 10


def main(out: Path) -> None:
    assert abs(sum(MIX.values()) - 1) < 1e-12
    full_h = FULL_MIN / 60
    contrib = {k: MIX[k] * TIER_H[k] for k in MIX}
    avg = sum(contrib.values())
    saving = 1 - avg / full_h
    close(full_h, 25.4, 0.05, "full acceptance hours")
    close(avg, 3.87, 0.005, "weighted average hours")
    close(saving, 0.85, 0.01, "saving fraction")
    result = {"exercise": "DC1", "evidence_label": "[MODELED]",
              "inputs": {"mix": MIX, "tier_hours": TIER_H, "full_acceptance_min": FULL_MIN},
              "steps": {k: round(v, 3) for k, v in contrib.items()},
              "answer": {"weighted_avg_h": round(avg, 3), "full_h": round(full_h, 2),
                         "saving_fraction": round(saving, 3)},
              "units": {"time": "h"}}
    rows = "\n".join(f"| {k} | {MIX[k]:.2f} | {TIER_H[k]:g} h | {contrib[k]:.3f} h |" for k in MIX)
    md = f"""
# DC1 result `[MODELED]`

| Repair type | Share | Tier duration | Contribution |
|---|---|---|---|
{rows}

Weighted average = {avg:.3f} h vs full acceptance {full_h:.1f} h → {saving * 100:.0f} % less.
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
