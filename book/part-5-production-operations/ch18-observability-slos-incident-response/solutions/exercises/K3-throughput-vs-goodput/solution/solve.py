"""K3 — A week with 100 % throughput SLI and 80 % goodput (Chapter 18).

Usage: python solve.py --out DIR
Writes result.json and result.md; asserts the answer key (solutions/exercises-key.md).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def emit(out: Path, result: dict, md: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8", newline="\n")


def close(value: float, key: float, tol: float, what: str) -> None:
    assert abs(value - key) <= tol, f"{what}: computed {value} vs key {key} (tol {tol})"


ALLOCATED_H, CRASH_EVERY_H, CKPT_INTERVAL_H = 168.0, 6.0, 1.0
RESTART_H, CANONICAL_RESTART_H = 0.7, 0.25


def goodput(restart_h: float) -> tuple[int, float, float]:
    crashes = int(ALLOCATED_H // CRASH_EVERY_H)
    lost = crashes * (CKPT_INTERVAL_H / 2 + restart_h)
    return crashes, lost, (ALLOCATED_H - lost) / ALLOCATED_H


def main(out: Path) -> None:
    crashes, lost, g = goodput(RESTART_H)
    _, lost_c, g_c = goodput(CANONICAL_RESTART_H)
    throughput_sli = 1.0         # every running minute at full speed
    assert crashes == 28
    close(lost, 33.6, 1e-9, "lost hours")
    close(g, 0.80, 1e-9, "goodput")
    close(g_c, 0.875, 1e-9, "goodput with canonical restart")
    result = {"exercise": "K3", "evidence_label": "[MODELED]",
              "inputs": {"allocated_h": ALLOCATED_H, "crash_every_h": CRASH_EVERY_H,
                         "checkpoint_interval_h": CKPT_INTERVAL_H, "restart_h": RESTART_H},
              "answer": {"crashes": crashes, "lost_h": round(lost, 2), "throughput_sli": throughput_sli,
                         "goodput": round(g, 4), "goodput_canonical_restart": round(g_c, 4),
                         "lost_h_canonical": round(lost_c, 2)},
              "units": {"time": "h", "sli": "fraction"}}
    md = f"""
# K3 result `[MODELED]`

- crashes = 168 / 6 = {crashes}; loss per crash = 0.5 + {RESTART_H} = {CKPT_INTERVAL_H / 2 + RESTART_H} h
- lost = {lost:.1f} h; goodput = (168 − {lost:.1f}) / 168 = {g:.3f}; throughput SLI = {throughput_sli:.0%}
- canonical 0.25 h restart: lost {lost_c:.1f} h, goodput {g_c:.3f}
"""
    emit(out, result, md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    main(Path(ap.parse_args().out))
