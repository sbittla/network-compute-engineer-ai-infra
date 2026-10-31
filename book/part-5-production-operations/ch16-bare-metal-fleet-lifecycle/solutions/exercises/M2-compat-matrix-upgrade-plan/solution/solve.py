"""M2 — Staged upgrade plan numbers for ORION (Chapter 16, Section 16.8).

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


# ORION parameters (docs/REFERENCE_CLUSTER.md) and Section 16.8 planning values [ILLUSTRATIVE]
NODES, RACKS, NODES_PER_RACK, GPUS_PER_NODE = 32, 8, 4, 8
CANARY_NODES, CANARY_BAKE_H = 2, 72.0
WAVE_CAP, RACK_CAP, WAVE_H, BAKE_H = 4, 1, 3.0, 12.0
LAMBDA = 0.01        # intermittent fault rate per node-hour


def main(out: Path) -> None:
    p_canary = 1 - math.exp(-LAMBDA * CANARY_NODES * CANARY_BAKE_H)
    nt_95 = math.log(20) / LAMBDA
    p_4x75 = 1 - math.exp(-LAMBDA * 4 * 75)
    remaining = NODES - CANARY_NODES
    waves = max(math.ceil(remaining / WAVE_CAP), math.ceil(NODES_PER_RACK / RACK_CAP))
    sizes = [WAVE_CAP] * (remaining // WAVE_CAP) + ([remaining % WAVE_CAP] if remaining % WAVE_CAP else [])
    calendar_h = (WAVE_H + CANARY_BAKE_H) + waves * (WAVE_H + BAKE_H)
    node_hours = NODES * WAVE_H
    gpu_hours = node_hours * GPUS_PER_NODE
    fraction = node_hours / (NODES * calendar_h)

    close(p_canary, 0.76, 0.005, "canary detection")
    close(nt_95, 300, 1.0, "node-hours for 95 %")
    close(p_4x75, 0.95, 0.001, "4 nodes x 75 h detection")
    assert waves == 8 and sizes == [4] * 7 + [2], sizes
    close(calendar_h, 195, 1e-9, "calendar hours")
    close(gpu_hours, 768, 0, "GPU-hours out")
    close(fraction, 0.015, 0.001, "capacity fraction")

    result = {"exercise": "M2", "evidence_label": "[MODELED]",
              "inputs": {"nodes": NODES, "racks": RACKS, "canary_nodes": CANARY_NODES, "canary_bake_h": CANARY_BAKE_H,
                         "wave_cap": WAVE_CAP, "per_rack_cap": RACK_CAP, "wave_h": WAVE_H, "bake_h": BAKE_H,
                         "lambda_per_node_hour": LAMBDA},
              "answer": {"canary_p_detect": round(p_canary, 4), "node_hours_for_95pct": round(nt_95, 1),
                         "p_detect_4_nodes_75_h": round(p_4x75, 4), "waves": waves, "wave_sizes": sizes,
                         "calendar_h": calendar_h, "calendar_days": round(calendar_h / 24, 2),
                         "node_hours_out": node_hours, "gpu_hours_out": gpu_hours,
                         "capacity_fraction": round(fraction, 4)},
              "units": {"time": "h", "capacity": "node-hours / GPU-hours"}}
    md = f"""
# M2 plan numbers `[MODELED]`

- Canary 2 × 72 h: P(detect) = 1 − exp(−0.01 × 144) = {p_canary * 100:.1f} %; 95 % needs {nt_95:.0f} node-hours (4 × 75 h → {p_4x75 * 100:.1f} %)
- Waves: max(ceil({remaining}/{WAVE_CAP}), {NODES_PER_RACK}) = {waves} ({sizes})
- Calendar: (3 + 72) + {waves} × (3 + 12) = {calendar_h:.0f} h = {calendar_h / 24:.1f} days
- Out of service: {node_hours:.0f} node-hours = {gpu_hours:.0f} GPU-hours = {fraction * 100:.1f} % of campaign capacity
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
