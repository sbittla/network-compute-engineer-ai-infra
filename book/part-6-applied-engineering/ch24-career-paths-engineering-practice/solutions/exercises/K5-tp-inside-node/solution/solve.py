#!/usr/bin/env python3
"""K5 — TP volume per GPU per step and its time over NVLink vs a NIC (W-TRAIN, Section 24.6)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Inputs: manuscript Section 24.6 ("Clarify", Table 24.9, "Memory -> parallelism") [MODELED]/[ILLUSTRATIVE]
SEQ_TOKENS = 4096            # tokens per sequence (one sequence per micro-batch)
HIDDEN = 8192                # hidden size
BYTES_PER_ELEM = 2           # BF16 activations
TP = 8                       # tensor-parallel group size (one HX8 node)
ALLREDUCES_PER_LAYER = 4     # two forward, two backward
LAYERS = 80
PP = 4
SEQS_PER_STEP = 1024
DP = 8
NVLINK_BPS = 360e9           # achieved NVLink per direction, 80 % of 450 GB/s [ILLUSTRATIVE]
NIC_BPS = 40e9               # achieved per-NIC bus bandwidth, 80 % of 50 GB/s [ILLUSTRATIVE]
STEP_S = 17.4                # modeled W-TRAIN step time [MODELED]

def write_outputs(out: Path, payload: dict, md_lines: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8", newline="\n")


def main_args() -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    return ap.parse_args().out


def main() -> None:
    out = main_args()
    act = SEQ_TOKENS * HIDDEN * BYTES_PER_ELEM                      # bytes per TP all-reduce payload
    ring = 2 * (TP - 1) / TP * act                                   # bytes each GPU sends per all-reduce
    layers_per_stage = LAYERS // PP
    micro = SEQS_PER_STEP // DP                                      # micro-batches per replica per step
    per_step = ring * ALLREDUCES_PER_LAYER * layers_per_stage * micro
    t_nv = per_step / NVLINK_BPS
    t_nic = per_step / NIC_BPS

    assert abs(act / 1e6 - 67.1) < 0.1, act
    assert abs(ring / 1e6 - 117) < 1, ring
    assert abs(per_step / 1e12 - 1.20) < 0.01, per_step                # key: 1.20 TB
    assert abs(t_nv - 3.3) < 0.1, t_nv                                 # key: ~3.3 s
    assert abs(t_nic - 30) < 0.5, t_nic                                # key: ~30 s
    assert t_nic > STEP_S

    payload = {
        "id": "K5", "evidence_label": "MODELED",
        "inputs": {"seq_tokens": SEQ_TOKENS, "hidden": HIDDEN, "bytes_per_elem": BYTES_PER_ELEM, "tp": TP,
                   "allreduces_per_layer": ALLREDUCES_PER_LAYER, "layers_per_stage": layers_per_stage,
                   "micro_batches": micro, "nvlink_GBps": NVLINK_BPS / 1e9, "nic_GBps": NIC_BPS / 1e9,
                   "step_s": STEP_S},
        "steps": {"activation_MB": round(act / 1e6, 2), "ring_bytes_per_allreduce_MB": round(ring / 1e6, 2),
                  "tp_bytes_per_gpu_per_step_TB": round(per_step / 1e12, 3)},
        "answer": {"time_over_nvlink_s": round(t_nv, 2), "time_over_nic_s": round(t_nic, 2),
                   "nic_time_exceeds_step": t_nic > STEP_S},
        "units": {"time": "s", "volume": "TB per GPU per step"},
    }
    md = [
        "# K5 — TP volume and time `[MODELED]`", "",
        f"- Activation per all-reduce: 4,096 × 8,192 × 2 B = {act / 1e6:.1f} MB",
        f"- Ring bytes per GPU: 2 × 7/8 × {act / 1e6:.1f} MB = {ring / 1e6:.1f} MB",
        f"- Per step per GPU: {ring / 1e6:.1f} MB × 4 × {layers_per_stage} × {micro} = {per_step / 1e12:.2f} TB",
        f"- Over NVLink at 360 GB/s: {t_nv:.2f} s",
        f"- Over a NIC at 40 GB/s: {t_nic:.1f} s, longer than the {STEP_S} s step",
    ]
    write_outputs(out, payload, md)


if __name__ == "__main__":
    main()
