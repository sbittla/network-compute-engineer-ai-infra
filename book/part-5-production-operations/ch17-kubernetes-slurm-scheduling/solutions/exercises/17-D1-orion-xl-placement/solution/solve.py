"""17-D1 — ORION-XL cross-block exposure and wait-time break-even (Chapter 17).

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


NODES_XL, BLOCK_NODES, RAILS, NIC_GBPS, OVERSUB = 512, 32, 8, 400, 2
JOB_NODES, GPUS_PER_NODE = 64, 8
SLOWDOWN, RUN_H = 0.03, 240.0          # [ILLUSTRATIVE]
CHOSEN_WAIT_H = 4.0


def main(out: Path) -> None:
    blocks_total = NODES_XL // BLOCK_NODES
    min_blocks = math.ceil(JOB_NODES / BLOCK_NODES)
    frac = {b: b / JOB_NODES for b in (2, 3)}
    per_block = JOB_NODES / blocks_total
    spread = 1 - (per_block - 1) / (JOB_NODES - 1)
    uplink_tbps = BLOCK_NODES * RAILS * NIC_GBPS / OVERSUB / 1000
    job_gpus = JOB_NODES * GPUS_PER_NODE
    slow_cost = SLOWDOWN * RUN_H * job_gpus
    breakeven = slow_cost / job_gpus
    wait_cost = CHOSEN_WAIT_H * job_gpus
    assert blocks_total == 16 and min_blocks == 2
    close(frac[2], 0.031, 0.0005, "2-block fraction")
    close(frac[3], 0.047, 0.0005, "3-block fraction")
    close(spread, 0.95, 0.005, "spread fraction")
    close(uplink_tbps, 51.2, 1e-9, "per-block uplink Tb/s")
    close(slow_cost, 3686, 1.0, "slowdown GPU-hours")
    close(breakeven, 7.2, 0.05, "break-even wait h")
    assert wait_cost < slow_cost
    result = {"exercise": "17-D1", "evidence_label": "[MODELED]",
              "inputs": {"nodes": NODES_XL, "block_nodes": BLOCK_NODES, "job_nodes": JOB_NODES,
                         "oversubscription": OVERSUB, "slowdown": SLOWDOWN, "run_h": RUN_H},
              "answer": {"blocks": blocks_total, "min_blocks": min_blocks,
                         "cross_block_fraction": {str(k): round(v, 4) for k, v in frac.items()},
                         "spread_cross_block_fraction": round(spread, 4),
                         "per_block_uplink_tbps": uplink_tbps, "slowdown_gpu_hours": round(slow_cost, 1),
                         "breakeven_wait_h": round(breakeven, 2), "chosen_wait_h": CHOSEN_WAIT_H,
                         "chosen_wait_cost_gpu_hours": wait_cost},
              "units": {"bandwidth": "Tb/s", "cost": "GPU-hours", "time": "h"}}
    md = f"""
# 17-D1 result `[MODELED]`

- min blocks = ceil({JOB_NODES}/{BLOCK_NODES}) = {min_blocks} of {blocks_total}
- cross-block hops: 2 blocks {frac[2] * 100:.1f} %, 3 blocks {frac[3] * 100:.1f} %, spread {spread * 100:.0f} %
- per-block uplink = {BLOCK_NODES} × {RAILS} × {NIC_GBPS} Gb/s / {OVERSUB} = {uplink_tbps:g} Tb/s
- slowdown cost = {SLOWDOWN} × {RUN_H:g} h × {job_gpus} = {slow_cost:,.0f} GPU-hours; break-even wait {breakeven:.1f} h
- chosen bound {CHOSEN_WAIT_H:g} h costs at most {wait_cost:,.0f} GPU-hours
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
