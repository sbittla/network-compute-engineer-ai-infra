"""14.12 -- The resume that trained worse: which checkpoint to restore and what it costs. [MODELED]

Usage: python solve.py --out DIR
Inputs: the incident log in the prompt (timestamps, steps, completion 18.9 s); W-TRAIN on 256 GPUs with
a 17.4 s step and the restart components in lab/data/orion_ckpt_inputs.yaml (soft restart, async PFS).
"""
import argparse
import json
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parents[4] / "lab" / "data"


def hms(t: str) -> int:
    h, m, s = (int(x) for x in t.split(":"))
    return h * 3600 + m * 60 + s


# prompt log
CKPTS = {88290: {"snapshot": "03:02:11", "commit": "03:02:30", "completion_s": 18.9, "has_commit": True},
         88327: {"snapshot": "03:12:55", "commit": None, "completion_s": None, "has_commit": False}}
FAILURE = "03:13:02"
DAMAGED_TRAINING_H = 2.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load((DATA / "orion_ckpt_inputs.yaml").read_text(encoding="utf-8"))
    w, s, r = cfg["workload"], cfg["storage"], cfg["restart"]
    gpus, step_s = w["gpus"], w["step_time_s"]

    # Which checkpoint is valid? Only committed ones, whose persist finished before the failure.
    t_fail = hms(FAILURE)
    secs_into_persist = t_fail - hms(CKPTS[88327]["snapshot"])
    valid = [st for st, c in CKPTS.items() if c["has_commit"] and hms(c["commit"]) < t_fail]
    restore = max(valid)
    assert restore == 88290 and secs_into_persist == 7 and secs_into_persist < CKPTS[88290]["completion_s"]

    size = float(w["params"]) * w["ckpt_bytes_per_param"]
    load_s = size / (s["pfs_read_GBps"] * 1e9 * s["pfs_efficiency"])
    soft_restart_s = r["detect_s"] + r["relaunch_s"] + r["validate_s"] + r["warmup_s"] + load_s
    damaged = DAMAGED_TRAINING_H * gpus
    recompute_steps = 88327 - restore
    recompute = recompute_steps * step_s * gpus / 3600
    restart = soft_restart_s * gpus / 3600
    total = damaged + recompute + restart
    # Key 14.12 (c): 512 + 45.8 + 57.5 ≈ 615 GPU-h (tolerance 0.1 GPU-h per term, 1 GPU-h total).
    assert abs(damaged - 512) < 0.1 and abs(recompute - 45.8) < 0.1 and abs(restart - 57.5) < 0.1
    assert abs(soft_restart_s - 808) < 0.5
    assert abs(total - 615) < 1, total

    result = {"inputs": {"checkpoints": CKPTS, "failure": FAILURE, "gpus": gpus, "step_time_s": step_s,
                         "damaged_training_h": DAMAGED_TRAINING_H, "restart": r},
              "steps": {"seconds_into_persist_at_failure": secs_into_persist, "valid_checkpoints": valid,
                        "load_s": round(load_s, 2), "soft_restart_s": round(soft_restart_s, 1),
                        "recompute_steps": recompute_steps, "recompute_s": round(recompute_steps * step_s, 1)},
              "answer": {"restore_from": f"step_{restore:06d}", "gpu_h_damaged": round(damaged, 1),
                         "gpu_h_recompute": round(recompute, 1), "gpu_h_restart": round(restart, 1),
                         "gpu_h_total": round(total, 1)},
              "units": {"cost": "GPU-hours", "time": "s"},
              "evidence_label": "[MODELED]"}
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = "\n".join([
        "# 14.12 recovery decision `[MODELED]`", "",
        f"- Failure {secs_into_persist} s into the ≈ 19 s persist of step 88327; no COMMIT -> invalid.",
        f"- Restore from step_{restore:06d} (committed 03:02:30).",
        f"- Damaged training: 2 h × {gpus} = {damaged:.0f} GPU-h",
        f"- Recompute {recompute_steps} steps × {step_s} s = {recompute_steps*step_s:.1f} s -> {recompute:.1f} GPU-h",
        f"- Soft restart {soft_restart_s:.1f} s -> {restart:.1f} GPU-h",
        f"- Total ≈ {total:.0f} GPU-h", ""])
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
