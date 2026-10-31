#!/usr/bin/env python3
"""K2: throughput loss of a synchronous job with one slow rank.

Usage: python solve.py --out DIR
Model [MODELED]: step time = max over ranks; the straggler runs at SPEED of its peers.
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

GPUS = 256          # ORION W-TRAIN job size
SPEED = 0.90        # "10 % slow": runs at 90 % of peer speed
GPU_HOUR_USD = 2.50  # [ILLUSTRATIVE], manuscript Section 1.7
KEY_LOSS = 0.10     # exercises-key.md K2: loss ~ 10 % of all 256 GPUs
KEY_GPU_EQ = 25.6
TOL = 1e-9


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    rank_times = [1.0] * (GPUS - 1) + [1.0 / SPEED]   # normalized step time per rank
    step = max(rank_times)                             # synchronous: the slowest rank sets the step
    throughput = 1.0 / step
    loss = 1.0 - throughput
    gpu_eq = loss * GPUS
    naive = (1 - SPEED) / GPUS
    alt_loss = 1 - 1 / 1.10                            # "takes 10 % longer" reading
    assert abs(loss - KEY_LOSS) < TOL, loss
    assert abs(gpu_eq - KEY_GPU_EQ) < 1e-6, gpu_eq
    assert naive < 0.001

    result = {"evidence": "[MODELED]", "inputs": {"gpus": GPUS, "straggler_speed": SPEED},
              "steps": {"step_time_normalized": round(step, 4), "throughput_fraction": round(throughput, 4)},
              "answer": {"throughput_loss": round(loss, 4), "gpu_equivalents_lost": round(gpu_eq, 2),
                         "naive_wrong_loss": round(naive, 6),
                         "loss_if_10pct_longer": round(alt_loss, 4),
                         "usd_per_hour_wasted": round(gpu_eq * GPU_HOUR_USD, 2)},
              "units": {"throughput_loss": "fraction", "gpu_equivalents_lost": "GPUs"}}
    md = ["# K2 — straggler arithmetic `[MODELED]`", "",
          f"- step time = max over ranks = 1 / {SPEED} = {step:.4f} T",
          f"- throughput = {throughput:.4f} of baseline, loss = {loss:.1%}",
          f"- GPU-equivalents lost = {loss:.2f} x {GPUS} = {gpu_eq:.1f}",
          f"- naive (wrong) 10 %/256 = {naive:.4%}",
          f"- if '10 % slow' means 10 % longer: loss = {alt_loss:.1%}"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
