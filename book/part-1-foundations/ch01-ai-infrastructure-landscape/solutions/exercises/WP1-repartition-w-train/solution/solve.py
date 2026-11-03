#!/usr/bin/env python3
"""WP1: TP 4 x PP 8 x DP 8 communication lower bounds for W-TRAIN, compared with TP 8 x PP 4.

Usage: python solve.py --out DIR
Inputs: W-TRAIN in docs/REFERENCE_CLUSTER.md; ceilings 450 GB/s NVLink, 50 GB/s NIC, 989 TFLOP/s.
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

PARAMS = 70e9
LAYERS = 80
HIDDEN = 8192
TOKENS = 4096 * 1024
BYTES = 2                     # BF16
NVLINK = 450e9                # B/s per direction
NIC = 50e9                    # B/s (400 Gb/s)
PEAK = 989e12                 # FLOP/s
GPUS = 256
M_MICRO = 64                  # micro-batches [ILLUSTRATIVE], for the bubble estimate
KEY = {"S_TP_GB": 343.6, "tp_sent_GB": 515.4, "T_scaleup_s": 1.145, "dp_sent_GB": 7.66,
       "T_dp_s": 0.153, "pp_sent_mid_GB": 4.30, "T_pp_s": 0.086, "nic_worst_GB": 11.95,
       "T_nic_worst_s": 0.239, "bubble_pp4": 0.045, "bubble_pp8": 0.099}
REL_TOL = 0.005


def ring(p: int) -> float:
    return 2 * (p - 1) / p


def layout(tp: int, pp: int, dp: int) -> dict:
    tokens_rep = TOKENS / dp
    payload = tokens_rep * HIDDEN * BYTES                 # one activation all-reduce, bytes
    s_tp = 4 * (LAYERS / pp) * payload                    # 2 fwd + 2 bwd per layer
    tp_sent = ring(tp) * s_tp
    params_gpu = PARAMS / (tp * pp)
    dp_sent = ring(dp) * params_gpu * BYTES
    pp_dir = payload / tp                                 # per GPU per direction (sequence parallel)
    pp_mid = 2 * pp_dir if pp > 2 else pp_dir
    compute = 6 * PARAMS * TOKENS / GPUS / PEAK
    return {"payload_GB": payload / 1e9, "S_TP_GB": s_tp / 1e9, "tp_sent_GB": tp_sent / 1e9,
            "T_scaleup_s": tp_sent / NVLINK, "params_per_gpu": params_gpu,
            "dp_sent_GB": dp_sent / 1e9, "T_dp_s": dp_sent / NIC,
            "pp_per_direction_GB": pp_dir / 1e9, "pp_sent_mid_GB": pp_mid / 1e9, "T_pp_s": pp_mid / NIC,
            "T_compute_s": compute}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    new = layout(4, 8, 8)
    new["nic_worst_GB"] = new["dp_sent_GB"] + new["pp_sent_mid_GB"]
    new["T_nic_worst_s"] = new["nic_worst_GB"] * 1e9 / NIC
    base = layout(8, 4, 8)
    # baseline Table 1.6 counts the middle-stage PP send as one direction pair split over 8 ranks
    base["nic_GB"] = base["dp_sent_GB"] + base["pp_sent_mid_GB"]
    base["T_nic_s"] = base["nic_GB"] * 1e9 / NIC
    bubble = {f"bubble_pp{p}": (p - 1) / (M_MICRO + p - 1) for p in (4, 8)}

    for k, v in KEY.items():
        got = bubble[k] if k.startswith("bubble") else new[k]
        tol = 0.001 if k.startswith("bubble") else REL_TOL * v
        assert abs(got - v) <= tol, (k, got, v)
    assert abs(base["tp_sent_GB"] - 1202.6) <= 0.5 and abs(base["T_scaleup_s"] - 2.67) <= 0.01
    assert abs(base["nic_GB"] - 9.8) <= 0.05 and abs(base["T_nic_s"] - 0.196) <= 0.001
    assert abs(new["T_compute_s"] - 6.958) <= 0.005

    def rnd(d: dict) -> dict:
        return {k: round(v, 4) for k, v in d.items()}

    result = {"evidence": "[MODELED]; m = 64 micro-batches [ILLUSTRATIVE]",
              "inputs": {"params": PARAMS, "layers": LAYERS, "hidden": HIDDEN, "tokens_per_step": TOKENS,
                         "nvlink_Bps": NVLINK, "nic_Bps": NIC},
              "answer": {"tp4_pp8_dp8": rnd(new), "tp8_pp4_dp8": rnd(base), "bubble": rnd(bubble)},
              "units": "GB, seconds, fractions"}
    md = ["# WP1 — TP 4 / PP 8 vs TP 8 / PP 4 `[MODELED]`", "",
          "| Per GPU per step | TP 8 / PP 4 | TP 4 / PP 8 |", "|---|---:|---:|",
          f"| TP bytes sent (GB) | {base['tp_sent_GB']:.1f} | {new['tp_sent_GB']:.1f} |",
          f"| NVLink bound (s) | {base['T_scaleup_s']:.3f} | {new['T_scaleup_s']:.3f} |",
          f"| DP bytes sent (GB) | {base['dp_sent_GB']:.2f} | {new['dp_sent_GB']:.2f} |",
          f"| PP bytes sent, middle stage (GB) | {base['pp_sent_mid_GB']:.2f} | {new['pp_sent_mid_GB']:.2f} |",
          f"| NIC worst case (GB / s) | {base['nic_GB']:.2f} / {base['T_nic_s']:.3f} | "
          f"{new['nic_worst_GB']:.2f} / {new['T_nic_worst_s']:.3f} |",
          f"| Compute bound (s) | {base['T_compute_s']:.2f} | {new['T_compute_s']:.2f} |",
          f"| 1F1B bubble at m = {M_MICRO} | {bubble['bubble_pp4']:.1%} | {bubble['bubble_pp8']:.1%} |"]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
