"""Exercise 4.13: wave quantization, a strided BF16 access pattern, and GEMM intensity vs batch.

Usage: python solve.py --out DIR
Inputs (prompt): 128 x 256 output tiles, 132 SMs; outputs 8,192 x 2,048 and 1,024 x 2,048; tensor
[8,192, 4,096] BF16 read along dimension 0; 32-B sectors (Section 4.4). Part (c) uses an illustrative
linear layer k = n = 4,096 to show that intensity ~ m when m << k, n.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SMS = 132
TILE_M, TILE_N = 128, 256
SHAPES = {"large": (8_192, 2_048), "small": (1_024, 2_048)}
KEY_EFF = {"large": 0.97, "small": 0.48}        # exercises-key.md 4.13 (a)
ROWS, COLS, BF16 = 8_192, 4_096, 2
WARP, SECTOR = 32, 32
KEY_COALESCE = 0.0625                            # (b)
K = N = 4_096                                   # (c) illustrative layer


def waves(m: int, n: int) -> dict:
    tiles = math.ceil(m / TILE_M) * math.ceil(n / TILE_N)
    w = tiles / SMS
    full = math.ceil(w)
    return {"tiles": tiles, "waves_exact": round(w, 3), "waves": full, "efficiency": round(w / full, 4)}


def intensity(m: int) -> float:
    return 2 * m * K * N / (BF16 * (m * K + K * N + m * N))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    a = {k: waves(*v) for k, v in SHAPES.items()}
    for k, v in a.items():
        assert abs(v["efficiency"] - KEY_EFF[k]) < 0.01, (k, v)
    stride_b = COLS * BF16
    sectors = len({t * stride_b // SECTOR for t in range(WARP)})
    useful = WARP * BF16
    coalesce = useful / (sectors * SECTOR)
    assert stride_b == 8_192 and sectors == 32 and coalesce == KEY_COALESCE
    c = {m: round(intensity(m), 1) for m in (512, 256, 128, 64)}
    ratio = intensity(64) / intensity(128)
    assert abs(ratio - 0.5) < 0.03, ratio   # halving m roughly halves intensity when m << k, n
    res = {"exercise": "4.13", "evidence_label": "MODELED",
           "inputs": {"sms": SMS, "tile": [TILE_M, TILE_N], "shapes": SHAPES, "tensor": [ROWS, COLS],
                      "dtype_bytes": BF16, "layer_k_n": [K, N]},
           "answer": {"a_waves": a,
                      "b_coalescing": {"thread_stride_B": stride_b, "sectors_per_warp": sectors,
                                       "useful_B": useful, "fetched_B": sectors * SECTOR, "efficiency": coalesce},
                      "c_intensity_flop_per_B_by_m": c, "c_ratio_m64_over_m128": round(ratio, 3)},
           "units": {"intensity": "FLOP/B", "bytes": "B"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Exercise 4.13 — waves, coalescing and intensity `[MODELED]`", "",
             "| Output | Tiles | Waves (exact → launched) | Wave efficiency |", "|---|---|---|---|"]
    for k, (m, n) in SHAPES.items():
        v = a[k]
        lines.append(f"| {m:,} × {n:,} | ({m:,} / 128) × ({n:,} / 256) = {v['tiles']} | {v['tiles']} / 132 = "
                     f"{v['waves_exact']:.2f} → {v['waves']} | {v['efficiency'] * 100:.0f} % |")
    lines += ["", f"(b) Adjacent threads are {COLS:,} × 2 B = {stride_b:,} B apart → {sectors} sectors × 32 B = "
              f"{sectors * SECTOR:,} B fetched for {useful} useful B = {coalesce * 100:.2f} %.", "",
              "(c) Intensity of a k = n = 4,096 BF16 linear layer: " +
              ", ".join(f"m = {m}: {v:,.1f} FLOP/B" for m, v in c.items()) +
              f". Halving m from 128 to 64 scales intensity by {ratio:.2f}."]
    (out / "result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
