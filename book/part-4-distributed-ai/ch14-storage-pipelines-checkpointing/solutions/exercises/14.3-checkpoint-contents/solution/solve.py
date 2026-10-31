"""14.3 -- Bytes per parameter: training state vs checkpoint (BF16 mixed precision + Adam). [MODELED]

Usage: python solve.py --out DIR
Inputs: manuscript Section 14.8 byte breakdown; W-TRAIN params from lab/data/orion_ckpt_inputs.yaml.
"""
import argparse
import json
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"

# component: (bytes per parameter, saved in checkpoint?)
COMPONENTS = {
    "bf16_weights": (2, True),
    "bf16_gradients": (2, False),     # recomputed by the first backward after resume
    "fp32_master_weights": (4, True),
    "adam_m_fp32": (4, True),
    "adam_v_fp32": (4, True),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "orion_ckpt_inputs.yaml").read_text(encoding="utf-8"))
    params = float(cfg["workload"]["params"])
    state = sum(b for b, _ in COMPONENTS.values())
    ckpt = sum(b for b, saved in COMPONENTS.values() if saved)
    # Key 14.3: 16 B/param training state, 14 B/param checkpoint (matches the lab YAML).
    assert state == 16 and ckpt == 14
    assert ckpt == cfg["workload"]["ckpt_bytes_per_param"]
    size_gb = params * ckpt / 1e9
    assert abs(size_gb - 980) < 0.5    # W-TRAIN checkpoint, Section 14.8

    result = {
        "inputs": {"components": {k: {"bytes_per_param": b, "checkpointed": s} for k, (b, s) in COMPONENTS.items()},
                   "params": params},
        "steps": {"training_state_B_per_param": state, "checkpoint_B_per_param": ckpt},
        "answer": {"training_state_B_per_param": state, "checkpoint_B_per_param": ckpt,
                   "w_train_checkpoint_GB": round(size_gb, 1),
                   "w_train_training_state_GB": round(params * state / 1e9, 1)},
        "units": {"size": "GB (1e9 B)", "per_param": "B/param"},
        "evidence_label": "[MODELED]",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# 14.3 result `[MODELED]`", "", "| Component | B/param | Checkpointed |", "|---|---|---|"]
    lines += [f"| {k} | {b} | {'yes' if s else 'no'} |" for k, (b, s) in COMPONENTS.items()]
    lines += ["", f"Training state {state} B/param; checkpoint {ckpt} B/param (gradients recomputed).",
              f"W-TRAIN: {params:.3g} × {ckpt} B = {size_gb:.0f} GB", ""]
    (out / "result.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
