"""Exercise 4.15: PCIe and pinned-memory budget for the HX8 input and step-overhead design.

Usage: python solve.py --out DIR
Inputs (prompt): 8 ranks, 100 MiB per rank per step, 60 ms target step, 1,400 optimizer tensors.
Assumptions (stated in answer.md): ~ 50 GB/s achievable pinned H2D per Gen5 x16 GPU link
[ILLUSTRATIVE]; two GPUs per PCIe switch (Figure R.1); 3 staging buffers per rank; 2 TiB host memory
per node (REFERENCE_CLUSTER.md); unfused AdamW ~ 5 elementwise launches per tensor (Lab 4's comb).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RANKS = 8
STEP_B = 100 * 2**20
STEP_S = 0.060
LINK_BPS = 50e9
GPUS_PER_SWITCH = 2
BUFFERS = 3
HOST_B = 2 * 2**40
TENSORS = 1_400
OPS_PER_TENSOR = 5
LAUNCH_US = 10.0          # CPU cost per launch, as in Exercise 4.9 / Section 4.5 [ILLUSTRATIVE]
KEY = {"per_gpu_GBps": 1.75, "link_share": 0.035, "per_switch_GBps": 3.5,
       "pinned_per_rank_MiB": 300, "pinned_per_node_MiB": 2_400}   # exercises-key.md 4.15
TOL = 0.01


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    per_gpu = STEP_B / STEP_S / 1e9
    share = per_gpu * 1e9 / LINK_BPS
    per_switch = per_gpu * GPUS_PER_SWITCH
    copy_ms = STEP_B / LINK_BPS * 1e3
    pinned_rank = BUFFERS * STEP_B / 2**20
    pinned_node = pinned_rank * RANKS
    pinned_node_gib = pinned_node / 1024
    host_share = pinned_node * 2**20 / HOST_B
    launches = TENSORS * OPS_PER_TENSOR
    launch_ms = launches * LAUNCH_US / 1e3
    for k, v in {"per_gpu_GBps": per_gpu, "link_share": share, "per_switch_GBps": per_switch,
                 "pinned_per_rank_MiB": pinned_rank, "pinned_per_node_MiB": pinned_node}.items():
        assert abs(v - KEY[k]) <= TOL * KEY[k], (k, v)
    assert abs(pinned_node_gib - 2.34) < 0.01, pinned_node_gib   # corrected key: 2,400 MiB = 2.34 GiB
    assert copy_ms < STEP_S * 1e3 / 10   # the copy fits in < 10 % of the step, so one-step-ahead prefetch hides it
    assert launch_ms > STEP_S * 1e3 / 10  # unfused optimizer launches would cost > 10 % of the step
    res = {"exercise": "4.15", "evidence_label": "MODELED",
           "inputs": {"ranks": RANKS, "bytes_per_rank_step": STEP_B, "step_s": STEP_S, "link_Bps": LINK_BPS,
                      "gpus_per_switch": GPUS_PER_SWITCH, "staging_buffers": BUFFERS, "host_bytes": HOST_B,
                      "optimizer_tensors": TENSORS, "launches_per_tensor_unfused": OPS_PER_TENSOR,
                      "cpu_us_per_launch": LAUNCH_US},
           "answer": {"per_gpu_GBps": round(per_gpu, 3), "link_share": round(share, 4),
                      "per_switch_uplink_GBps": round(per_switch, 2), "copy_ms_per_step": round(copy_ms, 2),
                      "pinned_per_rank_MiB": pinned_rank, "pinned_per_node_MiB": pinned_node,
                      "pinned_per_node_GiB": round(pinned_node_gib, 3), "pinned_share_of_host": round(host_share, 5),
                      "unfused_optimizer_launches": launches, "unfused_launch_cpu_ms": round(launch_ms, 1)},
           "units": {"bandwidth": "GB/s", "memory": "MiB/GiB", "time": "ms"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Exercise 4.15 — budgets `[MODELED]`

- Per-GPU input rate = 104,857,600 B / 0.060 s = {per_gpu:.2f} GB/s = {share * 100:.1f} % of ≈ 50 GB/s.
- Per PCIe switch (2 GPUs) = {per_switch:.1f} GB/s; copy time per step = 104,857,600 B / 50 × 10⁹ B/s = {copy_ms:.2f} ms.
- Pinned staging = 3 × 100 MiB = {pinned_rank:.0f} MiB per rank; × 8 = {pinned_node:,.0f} MiB = {pinned_node_gib:.2f} GiB per node
  ({host_share * 100:.2f} % of 2 TiB).
- Unfused optimizer ≈ 1,400 × 5 = {launches:,} launches ≈ {launch_ms:.0f} ms of CPU issue time at 10 µs each,
  more than the whole 60 ms step: fusion is mandatory.
"""
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
