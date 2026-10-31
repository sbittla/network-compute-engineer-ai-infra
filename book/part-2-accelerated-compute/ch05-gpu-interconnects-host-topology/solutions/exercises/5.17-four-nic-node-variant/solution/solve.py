"""Exercise 5.17: modeled busbw of a 4-NIC node variant vs HX8 for a 1 GiB all-reduce over 32 nodes.

Usage: python solve.py --out DIR
Model: Section 5.9 formula, deterministic (no variance). Parameters from lab/data/path_model.yaml
(PIX mean 48 GB/s, alpha 0.2 ms, shared_nic divides by sharers). n = 32 nodes x 8 GPUs = 256 ranks.
Variant: 8 GPUs, 4 NICs, GPU pair (2k, 2k+1) PIX to NIC k; NCCL still builds 8 rings, two per NIC.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

PARAMS = Path(__file__).resolve().parents[4] / "lab" / "data" / "path_model.yaml"
S = 2**30
NODES, GPUS = 32, 8
KEY = {"variant_busbw": 188.6, "hx8_busbw": 370.7, "variant_t_ms": 11.34}   # exercises-key.md 5.17
TOL = 0.1


def busbw(n: int, rings: int, size: float, ring_GBps: float, alpha_s: float) -> tuple[float, float]:
    f = 2 * (n - 1) / n
    t = f * (size / rings) / (ring_GBps * 1e9) + alpha_s
    return t, f * S / t / 1e9


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    p = yaml.safe_load(PARAMS.read_text(encoding="utf-8"))
    pix = p["classes"]["PIX"]["mean_GBps"]
    alpha = p["alpha_ms"] / 1e3
    n = NODES * GPUS
    t_hx8, bw_hx8 = busbw(n, 8, S, pix, alpha)
    t_v8, bw_v8 = busbw(n, 8, S, pix / 2, alpha)        # 8 rings, two share each NIC
    t_v4, bw_v4 = busbw(n, 4, S, pix, alpha)            # equivalently 4 rings at full NIC rate
    assert abs(bw_hx8 - KEY["hx8_busbw"]) < TOL and abs(bw_v8 - KEY["variant_busbw"]) < TOL
    assert abs(t_v8 * 1e3 - KEY["variant_t_ms"]) < 0.01 and abs(t_v8 - t_v4) < 1e-12
    res = {"exercise": "5.17", "evidence_label": "MODELED",
           "inputs": {"S_bytes": S, "nodes": NODES, "gpus_per_node": GPUS, "n": n, "pix_GBps": pix,
                      "alpha_ms": p["alpha_ms"], "params": "lab/data/path_model.yaml [ILLUSTRATIVE]"},
           "answer": {"hx8": {"rings": 8, "ring_GBps": pix, "t_ms": round(t_hx8 * 1e3, 3), "busbw_GBps": round(bw_hx8, 1)},
                      "variant_8_rings": {"ring_GBps": pix / 2, "t_ms": round(t_v8 * 1e3, 3), "busbw_GBps": round(bw_v8, 1)},
                      "variant_4_rings": {"ring_GBps": pix, "t_ms": round(t_v4 * 1e3, 3), "busbw_GBps": round(bw_v4, 1)},
                      "ratio": round(bw_v8 / bw_hx8, 3),
                      "per_node_nic_GBps": {"hx8": 8 * 50, "variant": 4 * 50}},
           "units": {"time": "ms", "busbw": "GB/s"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Exercise 5.17 — four-NIC variant vs HX8 `[MODELED]`

n = 32 × 8 = {n}; ring factor 2 × 255 / 256 = 1.99219; S / 8 = 134,217,728 B.

| Node | Rings × rate | t | busbw |
|---|---|---|---|
| HX8 (8 NICs) | 8 × {pix:.0f} GB/s | {t_hx8 * 1e3:.3f} ms | {bw_hx8:.1f} GB/s |
| Variant, 8 rings, 2 per NIC | 8 × {pix / 2:.0f} GB/s | {t_v8 * 1e3:.3f} ms | {bw_v8:.1f} GB/s |
| Variant, 4 rings of S/4 | 4 × {pix:.0f} GB/s | {t_v4 * 1e3:.3f} ms | {bw_v4:.1f} GB/s |

The variant reaches {bw_v8 / bw_hx8 * 100:.0f} % of HX8 busbw: per-node NIC bandwidth halves (200 vs 400 GB/s).
"""
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
