#!/usr/bin/env python3
"""K5: per-participant send factor of a bandwidth-optimal all-reduce, 2(p-1)/p.

Usage: python solve.py --out DIR
Also simulates a ring reduce-scatter + all-gather to count chunks sent, as an independent check.
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

KEY = {4: 1.5, 8: 1.75}   # exercises-key.md K5


def factor(p: int) -> float:
    return 2 * (p - 1) / p


def ring_chunks_sent(p: int) -> float:
    """Count bytes sent per rank in a ring all-reduce of S = 1 split into p chunks."""
    sent = [0.0] * p
    for _phase in ("reduce-scatter", "all-gather"):
        for _step in range(p - 1):
            for r in range(p):
                sent[r] += 1.0 / p          # each rank forwards one chunk to its neighbour
    assert len(set(sent)) == 1
    return sent[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    ans = {}
    for p, k in KEY.items():
        f = factor(p)
        assert abs(f - k) < 1e-12 and abs(ring_chunks_sent(p) - k) < 1e-12, p
        ans[str(p)] = f
    result = {"evidence": "[MODELED]", "formula": "sent = 2(p-1)/p x S", "answer": ans,
              "units": "multiples of S (bytes)"}
    md = ["# K5 — all-reduce send factor", ""] + [f"- p = {p}: 2({p}-1)/{p} = {v} S" for p, v in ans.items()]
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.md").write_text("\n".join(house(l) for l in md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
