"""12.10 — Six collectives on a 3-rank example and a simulated ring all-reduce.

Usage: python solve.py --out DIR      Evidence label: [MODELED]
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np


def rnd(obj, nd: int = 4):
    """Round floats for deterministic output."""
    if isinstance(obj, (bool, np.bool_)) or obj is None:
        return bool(obj) if isinstance(obj, np.bool_) else obj
    if isinstance(obj, (float, np.floating)):
        obj = float(obj)
        return float(f"{obj:.{nd}g}") if abs(obj) >= 1e6 or (obj != 0 and abs(obj) < 1e-3) else round(obj, nd)
    if isinstance(obj, dict):
        return {str(k): rnd(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rnd(v, nd) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


def emit(out: Path, result: dict, md: str, extra: dict | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(rnd(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8")
    for name, text in (extra or {}).items():
        (out / name).write_text(text, encoding="utf-8")
    print(md)

R = np.array([[2, 4, 6], [1, 3, 5], [10, 20, 30]])
ELEM_B = 4


def ring_allreduce(buf: np.ndarray) -> tuple[list[dict], np.ndarray, int]:
    n = buf.shape[0]
    b = buf.copy()
    steps, sent = [], 0
    for k in range(1, n):                                   # reduce-scatter
        msgs = [(r, (r + 1) % n, (r - k + 1) % n, int(b[r, (r - k + 1) % n])) for r in range(n)]
        for src, dst, c, v in msgs:
            b[dst, c] += v
        sent += 1
        steps.append({"step": f"RS {k}", "msgs": [f"R{s}->R{d} c{c}={v}" for s, d, c, v in msgs], "after": b.tolist()})
    for k in range(1, n):                                   # all-gather
        msgs = [(r, (r + 1) % n, (r - k + 2) % n, int(b[r, (r - k + 2) % n])) for r in range(n)]
        for src, dst, c, v in msgs:
            b[dst, c] = v
        sent += 1
        steps.append({"step": f"AG {k}", "msgs": [f"R{s}->R{d} c{c}={v}" for s, d, c, v in msgs], "after": b.tolist()})
    return steps, b, sent * ELEM_B


def solve() -> dict:
    n = R.shape[0]
    total = R.sum(axis=0)
    res = {
        "all_reduce": [total.tolist()] * n,
        "reduce_root0": [total.tolist(), R[1].tolist(), R[2].tolist()],
        "reduce_scatter": [[int(total[r])] for r in range(n)],
        "all_gather_first": [R[:, 0].tolist()] * n,
        "broadcast_root1": [R[1].tolist()] * n,
        "all_to_all": R.T.tolist(),
    }
    steps, final, bytes_sent = ring_allreduce(R)
    return {"inputs": {"ranks": R.tolist(), "elem_bytes": ELEM_B}, "results": res, "ring": steps,
            "answer": {"ring_final": final.tolist(), "bytes_per_rank": bytes_sent,
                       "formula_bytes": 2 * (n - 1) / n * R.shape[1] * ELEM_B, "steps": len(steps)},
            "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    x = r["results"]
    # Key 12.10 (exact).
    assert x["all_reduce"][0] == [13, 27, 41] and x["reduce_scatter"] == [[13], [27], [41]]
    assert x["all_gather_first"][0] == [2, 1, 10] and x["broadcast_root1"][0] == [1, 3, 5]
    assert x["all_to_all"] == [[2, 1, 10], [4, 3, 20], [6, 5, 30]]
    assert r["ring"][0]["after"] == [[2, 4, 36], [3, 3, 5], [10, 23, 30]]
    assert r["ring"][1]["after"] == [[2, 27, 36], [3, 3, 41], [13, 23, 30]]
    a = r["answer"]
    assert a["ring_final"] == [[13, 27, 41]] * 3 and a["steps"] == 4
    assert a["bytes_per_rank"] == 16 and abs(a["formula_bytes"] - 16) < 1e-9


def report(r: dict) -> str:
    lines = ["# 12.10 (O1) — Collectives by hand `[MODELED]`", ""]
    lines += [f"- {k}: {v}" for k, v in r["results"].items()]
    lines += ["", "| Step | Messages | Buffers after |", "|---|---|---|"]
    lines += [f"| {s['step']} | {', '.join(s['msgs'])} | {s['after']} |" for s in r["ring"]]
    a = r["answer"]
    lines += ["", f"Bytes per rank: {a['bytes_per_rank']} B; 2(n-1)/n x S = {a['formula_bytes']:.0f} B"]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    emit(out, r, report(r), extras(r) if "extras" in globals() else None)


if __name__ == "__main__":
    main()
