#!/usr/bin/env python3
"""TS (orion-n29): arithmetic behind the slow-replica diagnosis.

Usage: python solve.py --out DIR
Inputs are the prompt's [ILLUSTRATIVE] evidence table and W-INFER decode parameters (Section 1.9).
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

TPOT_SLOW_MS = 19.0
TPOT_FLEET_MS = 12.0
REPLICAS = 8                          # ORION's default inference pool, orion-n25..n32
DRAM_ACTIVE = {"n29": 0.41, "fleet": 0.63}
TENSOR_ACTIVE = {"n29": 0.05, "fleet": 0.08}
ALLREDUCES_PER_STEP = 2 * 80          # two per layer, 80 layers, decode has no backward pass
BATCH, HIDDEN, BYTES = 32, 8192, 2
NVLINK_BPS = 450e9
RING8 = 2 * 7 / 8
REPLAY_RATE_PER_S = 1.0
REPLAY_COST_S = 5e-6                  # generous upper bound per replay [ILLUSTRATIVE]
KEY = {"extra_us_per_allreduce": 44.0, "allreduces_per_s": 13_300, "partial_loss_extra_us": 1.0,
       "load_increase": 0.143, "tpot_worst_ms": 13.7}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    gap_s = (TPOT_SLOW_MS - TPOT_FLEET_MS) / 1e3
    extra_per_ar = gap_s / ALLREDUCES_PER_STEP
    ar_per_s = ALLREDUCES_PER_STEP / (TPOT_FLEET_MS / 1e3)
    msg = BATCH * HIDDEN * BYTES
    t_full = RING8 * msg / NVLINK_BPS
    t_partial = RING8 * msg / (NVLINK_BPS * 2 / 3)
    partial_extra = t_partial - t_full
    replay_per_step = REPLAY_RATE_PER_S * REPLAY_COST_S * TPOT_SLOW_MS / 1e3
    dram_expected = DRAM_ACTIVE["fleet"] * TPOT_FLEET_MS / TPOT_SLOW_MS
    tensor_expected = TENSOR_ACTIVE["fleet"] * TPOT_FLEET_MS / TPOT_SLOW_MS
    load_increase = REPLICAS / (REPLICAS - 1) - 1
    tpot_worst = TPOT_FLEET_MS * (1 + load_increase)   # upper bound: TPOT linear in load

    assert abs(extra_per_ar * 1e6 - KEY["extra_us_per_allreduce"]) <= 1.0
    assert abs(ar_per_s - KEY["allreduces_per_s"]) <= 100
    assert abs(partial_extra * 1e6 - KEY["partial_loss_extra_us"]) <= 0.1
    assert abs(load_increase - KEY["load_increase"]) <= 0.005
    assert abs(tpot_worst - KEY["tpot_worst_ms"]) <= 0.05 and tpot_worst < 50.0
    assert replay_per_step < 1e-3 * gap_s, "replays cannot explain the gap"
    assert abs(dram_expected - DRAM_ACTIVE["n29"]) <= 0.02 and abs(tensor_expected - TENSOR_ACTIVE["n29"]) <= 0.005

    ans = {"tpot_gap_ms": gap_s * 1e3, "extra_us_per_allreduce": extra_per_ar * 1e6,
           "allreduces_per_s": ar_per_s, "allreduce_msg_KB": msg / 1e3,
           "partial_loss_extra_us_per_allreduce": partial_extra * 1e6,
           "partial_loss_extra_ms_per_step": partial_extra * ALLREDUCES_PER_STEP * 1e3,
           "replay_cost_us_per_step": replay_per_step * 1e6,
           "dram_active_expected_if_waiting": dram_expected,
           "tensor_active_expected_if_waiting": tensor_expected,
           "load_increase_per_remaining_replica": load_increase,
           "tpot_p95_worst_case_ms": tpot_worst}
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] evidence", "answer": {k: round(v, 3) for k, v in ans.items()},
              "units": {"time": "us or ms as named", "load": "fraction"}}
    md = ["# TS — orion-n29 arithmetic `[MODELED]`", "",
          f"- gap {ans['tpot_gap_ms']:.1f} ms / {ALLREDUCES_PER_STEP} all-reduces = {ans['extra_us_per_allreduce']:.1f} us each",
          f"- all-reduces per second at 12 ms/step: {ans['allreduces_per_s']:.0f}",
          f"- replay cost per step: {ans['replay_cost_us_per_step']:.3f} us (negligible)",
          f"- partial NVLink loss (1/3): +{ans['partial_loss_extra_us_per_allreduce']:.2f} us per all-reduce, "
          f"+{ans['partial_loss_extra_ms_per_step']:.3f} ms per step",
          f"- DRAM active expected if the GPUs are only waiting: {dram_expected:.2f} (observed 0.41)",
          f"- load on the {REPLICAS - 1} remaining replicas: +{load_increase:.1%}",
          f"- worst-case TPOT p95 if linear in load: {tpot_worst:.1f} ms (SLO 50 ms)"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
