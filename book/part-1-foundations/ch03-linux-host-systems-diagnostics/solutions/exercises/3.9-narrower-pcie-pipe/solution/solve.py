#!/usr/bin/env python3
"""3.9: PCIe raw bandwidth, DP all-reduce cost of a Gen4 x16 rail NIC, and the repair decision.

Usage: python solve.py --out DIR
Inputs from the prompt and manuscript Section 3.11 [ILLUSTRATIVE]: 45 GB/s healthy rail, 82 % PCIe
efficiency, 17.4 s step, 256 GPUs, job MTBF 48 h, restart 15 min.
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

PARAMS, TP, PP, DP, BYTES = 70e9, 8, 4, 8, 2
HEALTHY_GBPS, PCIE_EFF, STEP_S, GPUS = 45.0, 0.82, 17.4, 256
MTBF_H, RESTART_H, REPLICA_GPUS = 48, 0.25, 32
KEY = {"gen5x16": 63.0, "gen4x16": 31.5, "gen4x2": 3.94, "gen1x16": 4.0, "sent_GB": 7.656,
       "healthy_s": 0.170, "degraded_s": 0.296, "extra_s": 0.126, "gpu_h_day": 44.0,
       "gen3x8_gpu_h_day": 339.0, "gen3x8_break_even_h": 2.4}


def raw(gts: float, lanes: int) -> float:
    enc = 128 / 130 if gts >= 8 else 8 / 10
    return gts * lanes * enc / 8


def cost(link_raw: float, sent: float) -> dict:
    t_ok = sent / HEALTHY_GBPS
    t_bad = sent / (PCIE_EFF * link_raw)
    extra = max(0.0, t_bad - t_ok)
    frac = extra / (STEP_S + extra)
    per_day = GPUS * 24 * frac
    per_hour = per_day / 24
    wait = MTBF_H * per_hour
    planned_fixed = RESTART_H * GPUS
    return {"t_degraded_s": t_bad, "extra_s": extra, "lost_fraction": frac, "gpu_h_day": per_day,
            "gpu_h_hour": per_hour, "wait_cost_gpu_h": wait, "shrink_gpu_h_hour": REPLICA_GPUS,
            "planned_break_even_h": (wait - planned_fixed) / GPUS, "keep_running_beats_shrink": per_hour < REPLICA_GPUS}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    links = {"gen5x16": raw(32, 16), "gen4x16": raw(16, 16), "gen4x2": raw(16, 2), "gen1x16": raw(2.5, 16)}
    sent = 2 * (DP - 1) / DP * PARAMS / (TP * PP) * BYTES / 1e9
    g4 = cost(links["gen4x16"], sent)
    g3 = cost(raw(8, 8), sent)
    got = {**links, "sent_GB": sent, "healthy_s": sent / HEALTHY_GBPS, "degraded_s": g4["t_degraded_s"],
           "extra_s": g4["extra_s"], "gpu_h_day": g4["gpu_h_day"], "gen3x8_gpu_h_day": g3["gpu_h_day"],
           "gen3x8_break_even_h": g3["planned_break_even_h"]}
    for k, v in KEY.items():
        assert abs(got[k] - v) <= 0.01 * v, (k, got[k], v)
    assert g4["keep_running_beats_shrink"] and g4["planned_break_even_h"] < 0.15   # planned stop never pays
    assert g3["keep_running_beats_shrink"]
    rnd = lambda d: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}
    result = {"evidence": "[MODELED] from [ILLUSTRATIVE] inputs",
              "answer": {"raw_GBps": rnd(links), "dp_sent_GB": round(sent, 4), "gen4x16": rnd(g4), "gen3x8": rnd(g3),
                         "decision_gen4x16": "keep running; repair at the next unplanned restart"},
              "units": {"bandwidth": "GB/s per direction", "time": "s", "cost": "GPU-hours"}}
    md = ["# 3.9 `[MODELED]`", ""] + [f"- {k}: {v:.2f} GB/s raw" for k, v in links.items()]
    md += [f"- DP all-reduce sent {sent:.3f} GB; healthy {sent / HEALTHY_GBPS:.3f} s; Gen4 x16 {g4['t_degraded_s']:.3f} s",
           f"- extra <= {g4['extra_s']:.3f} s/step -> {g4['gpu_h_day']:.1f} GPU-h/day ({g4['gpu_h_hour']:.2f}/h vs shrink 32/h)",
           f"- waiting {g4['wait_cost_gpu_h']:.0f} GPU-h; planned stop pays only if repair < {g4['planned_break_even_h'] * 60:.1f} min",
           f"- Gen3 x8: {g3['gpu_h_day']:.0f} GPU-h/day; planned stop pays if repair < {g3['planned_break_even_h']:.2f} h"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
