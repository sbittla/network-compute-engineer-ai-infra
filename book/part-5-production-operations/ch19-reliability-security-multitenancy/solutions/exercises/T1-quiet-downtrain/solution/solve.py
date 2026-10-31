"""T1 — the quiet downtrain: x16 vs x8 bandwidth, NIC deficit, and the restart break-even (Section 19.3, 19.6).

    python solve.py --out DIR

All evidence values come from the prompt (`[ILLUSTRATIVE]`); PCIe rates from the Gen5 line code and
docs/VERIFIED_FACTS.md; restart overhead R = 15 min from the Reference Cluster. Results `[MODELED]`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

GT, ENC = 32.0, 128 / 130            # Gen5 per lane, 128b/130b
X8_ACHIEVABLE_GBS = (25.0, 27.5)      # VERIFIED_FACTS.md (200–220 Gb/s)
NIC_GBS = 400 / 8                     # 400 Gb/s backend NIC
PEER_TX_GBITS = (1050.0, 1080.0)      # prompt: 15 healthy nodes, 8 NICs summed
N10_TX_GBITS = 985.0                  # prompt: orion-n10
SLOWDOWN = 0.09                       # prompt: job 9 % slower
JOB_GPUS = 16 * 8
LOST_WORK_MIN = 15.0                  # key: ≈ 15 min of work since the last checkpoint (avg half-interval)
RESTART_MIN = 15.0                    # REFERENCE_CLUSTER.md restart overhead

# solutions/exercises-key.md, T1
KEY = {"x16": 63.0, "x8": 31.5, "restart_cost_gpu_h": 64.0, "break_even_h": 5.6, "nic_deficit": 0.07}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    x16 = GT * 16 * ENC / 8
    x8 = GT * 8 * ENC / 8
    peer_mid = sum(PEER_TX_GBITS) / 2
    deficit = 1 - N10_TX_GBITS / peer_mid
    deficit_range = (1 - N10_TX_GBITS / PEER_TX_GBITS[0], 1 - N10_TX_GBITS / PEER_TX_GBITS[1])
    restart_cost = JOB_GPUS * (LOST_WORK_MIN + RESTART_MIN) / 60
    loss_rate = JOB_GPUS * SLOWDOWN          # GPU-h wasted per wall-clock hour of degraded running
    break_even_h = restart_cost / loss_rate

    assert abs(x16 - KEY["x16"]) < 0.1 and abs(x8 - KEY["x8"]) < 0.1
    assert x8 < NIC_GBS and X8_ACHIEVABLE_GBS[1] < NIC_GBS
    assert abs(deficit - KEY["nic_deficit"]) < 0.01, deficit
    assert restart_cost == KEY["restart_cost_gpu_h"]
    assert abs(break_even_h - KEY["break_even_h"]) < 0.05, break_even_h

    result = {
        "exercise": "T1",
        "inputs": {"peer_tx_gbits": list(PEER_TX_GBITS), "n10_tx_gbits": N10_TX_GBITS, "slowdown": SLOWDOWN,
                   "job_gpus": JOB_GPUS, "lost_work_min": LOST_WORK_MIN, "restart_min": RESTART_MIN},
        "steps": {"x16_gbs": round(x16, 2), "x8_gbs": round(x8, 2), "x8_achievable_gbs": list(X8_ACHIEVABLE_GBS),
                  "nic_line_rate_gbs": NIC_GBS, "n10_tx_deficit_vs_peer_mid": round(deficit, 3),
                  "n10_tx_deficit_range": [round(v, 3) for v in deficit_range],
                  "restart_cost_gpu_h": round(restart_cost, 1), "degraded_loss_gpu_h_per_h": round(loss_rate, 2)},
        "answer": {"x16_gbs": round(x16, 1), "x8_gbs": round(x8, 1), "break_even_remaining_runtime_h": round(break_even_h, 1),
                   "decision": "requeue onto a replacement node if remaining runtime > ~5.6 h; else finish and repair after"},
        "units": {"bandwidth": "GB/s per direction", "cost": "GPU-h", "time": "h"},
        "evidence_label": "[MODELED] from [ILLUSTRATIVE] evidence",
        "tolerance": "±0.1 GB/s; ±0.01 deficit; ±0.05 h",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    md = ["# T1 — The quiet downtrain `[MODELED]`", "",
          f"- Gen5 x16: 32 × 16 × 128/130 / 8 = {x16:.1f} GB/s/dir; x8: {x8:.1f} GB/s/dir "
          f"(≈ {X8_ACHIEVABLE_GBS[0]:.0f}–{X8_ACHIEVABLE_GBS[1]:.1f} achievable) < {NIC_GBS:.0f} GB/s NIC line rate",
          f"- orion-n10 NIC TX {N10_TX_GBITS:,.0f} Gb/s vs peers {PEER_TX_GBITS[0]:,.0f}–{PEER_TX_GBITS[1]:,.0f}: "
          f"{deficit_range[0] * 100:.1f} %–{deficit_range[1] * 100:.1f} % lower (≈ {deficit * 100:.1f} %)",
          f"- Restart cost = {JOB_GPUS} GPUs × ({LOST_WORK_MIN:.0f} + {RESTART_MIN:.0f}) min = {restart_cost:.0f} GPU-h; "
          f"degraded running wastes {JOB_GPUS} × {SLOWDOWN} = {loss_rate:.2f} GPU-h per hour",
          f"- Break-even remaining runtime = {restart_cost:.0f} / {loss_rate:.2f} = {break_even_h:.1f} h"]
    (out / "result.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
