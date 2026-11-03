"""12.20 — All-to-all bytes, busbw and spine share with and without PXN on ORION.

Usage: python solve.py --out DIR      Evidence label: [MODELED]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

GPUS_PER_NODE = 8
NIC_GBPS = 45.0                 # effective GB/s per 400 Gb/s NIC (Chapter 11, Table 11.4)
S_BYTES = 1 << 30               # 1 GiB per rank


def rnd(obj, nd: int = 4):
    """Round floats for deterministic output."""
    if isinstance(obj, float):
        return float(f"{obj:.{nd}g}") if abs(obj) >= 1e6 or (obj != 0 and abs(obj) < 1e-3) else round(obj, nd)
    if isinstance(obj, dict):
        return {str(k): rnd(v, nd) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [rnd(v, nd) for v in obj]
    return obj


def alltoall(nodes: int, s_bytes: int = S_BYTES) -> dict:
    """Rail-optimized all-to-all over `nodes` HX8 nodes, one rank per GPU.

    Each rank sends s/n to each of n - 1 peers. Every NIC carries (nodes - 1)/nodes * s per direction
    with or without PXN, so time = that / NIC rate. Without PXN, a chunk to another node on a different
    GPU index leaves on the source rail and crosses a spine; with PXN it is first moved over NVLink to
    the GPU on the destination rail, and ORION's rail leaves reach every node, so no byte uses a spine.
    """
    n = nodes * GPUS_PER_NODE
    chunk = s_bytes / n
    intra = (GPUS_PER_NODE - 1) * chunk
    same_rail = (nodes - 1) * chunk
    cross_rail = (nodes - 1) * (GPUS_PER_NODE - 1) * chunk
    sent = (n - 1) * chunk
    nic_bytes = (nodes - 1) / nodes * s_bytes
    t_s = nic_bytes / (NIC_GBPS * 1e9)
    algbw = s_bytes / t_s / 1e9
    return {"n": n, "chunk_MB": chunk / 1e6, "intra_MB": intra / 1e6, "same_rail_MB": same_rail / 1e6,
            "cross_rail_MB": cross_rail / 1e6, "sent_MB": sent / 1e6, "nic_MB_per_direction": nic_bytes / 1e6,
            "time_ms": t_s * 1e3, "algbw_GBps": algbw, "busbw_GBps": algbw * (n - 1) / n,
            "spine_fraction_pxn_off": cross_rail / sent, "spine_fraction_pxn_on": 0.0,
            "cross_rail_share_of_internode": cross_rail / (same_rail + cross_rail)}


def solve() -> dict:
    return {"inputs": {"gpus_per_node": GPUS_PER_NODE, "nic_GBps": NIC_GBPS, "S_bytes": S_BYTES},
            "two_nodes": alltoall(2), "orion_256": alltoall(32),
            "units": {"bytes": "MB (1e6 B)", "time": "ms", "bw": "GB/s"}, "evidence_label": "[MODELED]"}


def check(r: dict) -> None:
    a, b = r["two_nodes"], r["orion_256"]
    # Key 12.20 (tolerance 0.1 MB / 0.01 ms / 0.1 GB/s / 0.001).
    assert abs(a["chunk_MB"] - 67.1) < 0.1 and abs(a["intra_MB"] - 469.8) < 0.1 and abs(a["cross_rail_MB"] - 469.8) < 0.1
    assert abs(a["same_rail_MB"] - 67.1) < 0.1 and abs(a["nic_MB_per_direction"] - 536.9) < 0.1
    assert abs(a["time_ms"] - 11.93) < 0.01 and abs(a["algbw_GBps"] - 90.0) < 0.1 and abs(a["busbw_GBps"] - 84.4) < 0.1
    assert abs(a["spine_fraction_pxn_off"] - 7 / 15) < 1e-3 and a["cross_rail_share_of_internode"] == 7 / 8
    assert abs(b["time_ms"] - 23.12) < 0.01 and abs(b["busbw_GBps"] - 46.3) < 0.1
    assert abs(b["spine_fraction_pxn_off"] - 217 / 255) < 1e-3


def report(r: dict) -> str:
    a, b = r["two_nodes"], r["orion_256"]
    return f"""# 12.20 — All-to-all and PXN `[MODELED]`

| Case | n | Chunk (MB) | NIC bytes/dir (MB) | Time (ms) | algbw (GB/s) | busbw (GB/s) | Spine share, PXN off | PXN on |
|---|---|---|---|---|---|---|---|---|
| 2 nodes | {a['n']} | {a['chunk_MB']:.1f} | {a['nic_MB_per_direction']:.1f} | {a['time_ms']:.2f} | {a['algbw_GBps']:.1f} | {a['busbw_GBps']:.1f} | {a['spine_fraction_pxn_off'] * 100:.1f} % | 0 % |
| 32 nodes | {b['n']} | {b['chunk_MB']:.2f} | {b['nic_MB_per_direction']:.1f} | {b['time_ms']:.2f} | {b['algbw_GBps']:.1f} | {b['busbw_GBps']:.1f} | {b['spine_fraction_pxn_off'] * 100:.1f} % | 0 % |

Two nodes, per rank: intra-node {a['intra_MB']:.1f} MB, same-rail {a['same_rail_MB']:.1f} MB, cross-rail {a['cross_rail_MB']:.1f} MB.
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    out = ap.parse_args().out
    r = solve()
    check(r)
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(rnd(r), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = report(r)
    (out / "result.md").write_text(md.strip() + "\n", encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
