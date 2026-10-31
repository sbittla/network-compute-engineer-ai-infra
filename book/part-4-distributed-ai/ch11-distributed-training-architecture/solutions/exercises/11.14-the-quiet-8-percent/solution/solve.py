"""11.14 — Rank-to-node mapping and GPU-hours lost to one power-capped node.

Usage: python solve.py --out DIR      Evidence label: [MODELED] (assumptions [ILLUSTRATIVE], Table 11.4)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml


def rnd(obj, nd: int = 4):
    """Round floats for deterministic output: 4 significant digits for very large/small, else nd decimals."""
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, float):
        if obj != obj:
            return None
        return float(f"{obj:.{nd}g}") if abs(obj) >= 1e6 or (obj != 0 and abs(obj) < 1e-3) else round(obj, nd)
    if isinstance(obj, dict):
        return {str(k): rnd(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rnd(v, nd) for v in obj]
    return obj


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(rnd(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8")
    print(md)

TP, DP, PP, GPN, GPUS = 8, 8, 4, 8, 256
SLOW_RANKS = range(96, 104)
BASE_STEP_S = 17.45
EXTRA_WAIT_S = 1.3            # compute 15.2 s vs 13.9 s on the slow node
M, P = 128, 4                 # micro-batches and stages: the wait scales with (m + p - 1)/m


def solve() -> dict:
    nodes = sorted({r // GPN for r in SLOW_RANKS})
    coords = sorted({((r // TP) % DP, r // (TP * DP)) for r in SLOW_RANKS})
    expected = BASE_STEP_S + EXTRA_WAIT_S * (M + P - 1) / M
    loss_frac = 1 - BASE_STEP_S / expected
    return {"inputs": {"slow_ranks": [SLOW_RANKS.start, SLOW_RANKS.stop - 1], "baseline_step_s": BASE_STEP_S},
            "mapping": {"node_index": nodes, "hostname": [f"orion-n{n + 1:02d}" for n in nodes],
                        "dp_pp": [{"dp": d, "pp": p} for d, p in coords], "is_one_tp_group": len(coords) == 1},
            "answer": {"expected_step_s": expected, "throughput_loss": loss_frac,
                       "gpu_h_lost_per_day": loss_frac * GPUS * 24},
            "units": {"step": "s", "loss": "GPU-hours per day"}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    m, a = r["mapping"], r["answer"]
    # Key 11.14: orion-n13 (index 12), PP stage 1, DP replica 4; 18.78 s; ~435 GPU-h/day (tol 2 GPU-h).
    assert m["hostname"] == ["orion-n13"] and m["dp_pp"] == [{"dp": 4, "pp": 1}] and m["is_one_tp_group"]
    assert abs(a["expected_step_s"] - 18.78) < 0.005
    assert abs(a["gpu_h_lost_per_day"] - 435) < 2


def report(r: dict) -> str:
    m, a = r["mapping"], r["answer"]
    return f"""# 11.14 — The quiet 8 % `[MODELED]`

ranks 96-103 -> {m['hostname'][0]} (node index {m['node_index'][0]}), DP replica {m['dp_pp'][0]['dp']}, PP stage {m['dp_pp'][0]['pp']}
expected step = 17.45 + 1.3 x 131/128 = {a['expected_step_s']:.2f} s
loss = 1 - 17.45/{a['expected_step_s']:.2f} = {a['throughput_loss'] * 100:.1f} % -> {a['gpu_h_lost_per_day']:.0f} GPU-h per day
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r))


if __name__ == "__main__":
    main()
