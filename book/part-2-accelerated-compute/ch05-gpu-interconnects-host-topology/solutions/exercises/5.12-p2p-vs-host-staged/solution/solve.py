"""Exercise 5.12: 4 GiB GPU2 -> GPU6 over NVLink P2P vs host-staged PCIe, unpipelined and pipelined.

Usage: python solve.py --out DIR
Inputs (prompt): 4 GiB, 370 GB/s NVLink, 52 GB/s PCIe per direction, 64 MiB chunks.
Pipelined model: the two legs overlap chunk by chunk, so time = one full leg + one chunk on the other leg.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SIZE = 4 * 2**30
NVLINK_BPS = 370e9
PCIE_BPS = 52e9
CHUNK = 64 * 2**20
KEY_MS = {"nvlink": 11.6, "staged_unpipelined": 165.2, "staged_pipelined": 83.9}   # exercises-key.md 5.12 (c)
TOL = 0.005  # relative


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    leg = SIZE / PCIE_BPS
    chunks = SIZE // CHUNK
    got = {"nvlink": SIZE / NVLINK_BPS * 1e3,
           "staged_unpipelined": 2 * leg * 1e3,
           "staged_pipelined": (leg + CHUNK / PCIE_BPS) * 1e3}
    for k, v in got.items():
        assert abs(v - KEY_MS[k]) <= TOL * KEY_MS[k], (k, v)
    res = {"exercise": "5.12", "evidence_label": "MODELED",
           "inputs": {"bytes": SIZE, "nvlink_Bps": NVLINK_BPS, "pcie_Bps": PCIE_BPS, "chunk_bytes": CHUNK},
           "steps": {"pcie_leg_ms": round(leg * 1e3, 2), "chunks": chunks, "chunk_ms": round(CHUNK / PCIE_BPS * 1e3, 3)},
           "answer": {f"{k}_ms": round(v, 1) for k, v in got.items()},
           "units": {"time": "ms"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Exercise 5.12 — transfer times `[MODELED]`

4 GiB = {SIZE:,} B.

| Path | Formula | Time |
|---|---|---|
| NVLink P2P | {SIZE:,} B / 370 × 10⁹ B/s | {got['nvlink']:.1f} ms |
| Host-staged, unpipelined | 2 × {SIZE:,} B / 52 × 10⁹ B/s = 2 × {leg * 1e3:.1f} ms | {got['staged_unpipelined']:.1f} ms |
| Host-staged, 64 MiB chunks ({chunks} chunks) | {leg * 1e3:.1f} ms + 67,108,864 B / 52 × 10⁹ B/s | {got['staged_pipelined']:.1f} ms |

NVLink is {got['staged_pipelined'] / got['nvlink']:.1f}× faster than the best host-staged path.
"""
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
