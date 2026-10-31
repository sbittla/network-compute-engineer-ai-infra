"""13.14 -- Per-rank straggler telemetry volume for a 4,096-GPU ORION-XL job. [MODELED]

Usage: python solve.py --out DIR
Inputs ([ILLUSTRATIVE] design choices, stated in answer.md): 4,096 ranks, 20 numeric fields of
8 B, one row per rank every 10 steps, 2 s step. Also the per-step variant and a DCGM 1 Hz stream.
"""
import argparse
import json
from pathlib import Path

RANKS = 4096
FIELDS = 20
BYTES_PER_FIELD = 8
STEP_S = 2.0
STRIDE_STEPS = 10
DCGM_FIELDS = 10          # per GPU, 1 Hz node-agent stream
DAY_S = 86400


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    steps_day = DAY_S / STEP_S
    samples_day = steps_day / STRIDE_STEPS
    bytes_sample = RANKS * FIELDS * BYTES_PER_FIELD
    vol = bytes_sample * samples_day
    vol_every_step = bytes_sample * steps_day
    dcgm = RANKS * DCGM_FIELDS * BYTES_PER_FIELD * DAY_S
    # Key 13.14: 4,096 × 20 × 8 B × (86,400 / 2 / 10) ≈ 2.8 GB/day before compression (tol 0.01 GB).
    assert abs(vol / 1e9 - 2.83) < 0.01, vol

    result = {
        "inputs": {"ranks": RANKS, "fields": FIELDS, "bytes_per_field": BYTES_PER_FIELD,
                   "step_s": STEP_S, "stride_steps": STRIDE_STEPS, "dcgm_fields": DCGM_FIELDS},
        "steps": {"steps_per_day": steps_day, "samples_per_day": samples_day,
                  "bytes_per_sample": bytes_sample},
        "answer": {"per_rank_GB_per_day": round(vol / 1e9, 2),
                   "per_rank_every_step_GB_per_day": round(vol_every_step / 1e9, 1),
                   "dcgm_1hz_GB_per_day": round(dcgm / 1e9, 1)},
        "units": {"volume": "GB/day (1e9 B), before compression"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = (f"# 13.14 volume estimate `[MODELED]`\n\n"
          f"- steps/day = 86,400 / {STEP_S:.0f} = {steps_day:,.0f}; sampled every {STRIDE_STEPS} -> {samples_day:,.0f}\n"
          f"- bytes/sample = {RANKS:,} × {FIELDS} × {BYTES_PER_FIELD} B = {bytes_sample:,} B\n"
          f"- per-rank stream = {vol/1e9:.2f} GB/day (every step: {vol_every_step/1e9:.1f} GB/day)\n"
          f"- DCGM 1 Hz, {DCGM_FIELDS} fields/GPU = {dcgm/1e9:.1f} GB/day (node agent, already collected)\n")
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
