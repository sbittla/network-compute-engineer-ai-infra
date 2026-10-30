#!/usr/bin/env python3
"""Generate synthetic nccl-tests ``all_reduce_perf`` outputs for the Chapter 12 lab (deterministic).

The files imitate the text format printed by NVIDIA's nccl-tests ``all_reduce_perf`` (one MPI
process per GPU, ``-b 8 -e 8G -f 2 -g 1``): a parameter header, the "Using devices" table, the
out-of-place / in-place result table, and the trailer. Timing follows an alpha-beta model with a
medium-size protocol/pipelining inefficiency and seeded multiplicative noise:

    T(S) = alpha + 2(n-1)/n * S / B * (1 + 0.6 * exp(-S / 1 MiB)) * noise

Every number is [SIMULATED] and [ILLUSTRATIVE] — chosen to resemble published H100-class results in
shape, not copied from any measurement. Instructor notes in ``solutions/`` document which
configurations carry planted problems.

Usage:
    python tools/generate_data.py          # writes ../data/*.log, ../data/configs.yaml, ../data/nccl_debug_*.txt
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import yaml

SEED = 12
BUS_IDS = ["0x18", "0x2a", "0x3a", "0x5d", "0x9a", "0xab", "0xba", "0xdb"]
SIZES = [8 * 2**k for k in range(31)]          # 8 B .. 8 GiB, factor 2

# name, nodes, alpha_us, busbw_GBps, noise_small, noise_large, description (learner-visible)
CONFIGS = [
    ("c1_1node_8gpu", 1, 14.0, 450.0, 0.02, 0.005, "1 x HX8, 8 GPUs, NVLink/NVSwitch only (NVLS in-switch reduction enabled)"),
    ("c2_2node_aligned", 2, 28.0, 355.0, 0.03, 0.008, "2 x HX8, 16 GPUs, default rank map (8 ranks per node, GPU i -> NIC i)"),
    ("c3_2node_alt_map", 2, 39.0, 185.0, 0.03, 0.008, "2 x HX8, 16 GPUs, alternative container image and rank/NIC map"),
    ("c4_4node_aligned", 4, 36.0, 350.0, 0.03, 0.008, "4 x HX8, 32 GPUs, default rank map"),
    ("c5_8node_aligned", 8, 47.0, 346.0, 0.03, 0.010, "8 x HX8, 64 GPUs, default rank map (nodes orion-n01 to orion-n08)"),
    ("c6_8node_run2", 8, 50.0, 190.0, 0.03, 0.090, "8 x HX8, 64 GPUs, same job as c5 one day later (nodes orion-n01 to orion-n07, orion-n12)"),
]


def times_us(rng: np.random.Generator, n: int, alpha: float, bw: float, ns: float, nl: float) -> np.ndarray:
    """Simulated all-reduce times in microseconds for every size in SIZES."""
    f = 2 * (n - 1) / n
    s = np.array(SIZES, dtype=float)
    ideal = alpha + f * s / (bw * 1e9) * 1e6 * (1 + 0.6 * np.exp(-s / 2**20))
    sigma = np.where(s < 2**20, ns, nl)
    return ideal * np.exp(rng.normal(0.0, sigma))


def fmt_time(t_us: float) -> str:
    """nccl-tests prints time with precision that shrinks as the value grows (7 characters wide)."""
    if t_us >= 10000.0:
        return f"{t_us:7.0f}"
    if t_us >= 100.0:
        return f"{t_us:7.1f}"
    return f"{t_us:7.2f}"


def render(name: str, nodes: int, t_oop: np.ndarray, t_ip: np.ndarray, rng: np.random.Generator) -> str:
    n = nodes * 8
    lines = [
        "# nThread 1 nGpus 1 minBytes 8 maxBytes 8589934592 step: 2(factor) warmup iters: 5 iters: 20 "
        "agg iters: 1 validation: 1 graph: 0",
        "#",
        "# Using devices",
    ]
    for r in range(n):
        host = f"orion-n{(r // 8) + 1:02d}"
        if name == "c6_8node_run2" and r // 8 == 7:
            host = "orion-n12"
        pid = 41000 + int(rng.integers(0, 900)) + r
        lines.append(f"#  Rank {r:2d} Group  0 Pid {pid:6d} on {host:>8s} device  {r % 8} "
                     f"[{BUS_IDS[r % 8]}] NVIDIA H100 80GB HBM3")
    lines += [
        "#",
        "#                                                              out-of-place                       in-place          ",
        "#       size         count      type   redop    root     time   algbw   busbw #wrong     time   algbw   busbw #wrong",
        "#        (B)    (elements)                               (us)  (GB/s)  (GB/s)            (us)  (GB/s)  (GB/s)       ",
    ]
    f = 2 * (n - 1) / n
    busbws = []
    for i, size in enumerate(SIZES):
        row = f"{size:12d}  {size // 4:12d}     float     sum      -1"
        for t in (float(fmt_time(t_oop[i])), float(fmt_time(t_ip[i]))):
            algbw = size / (t * 1e-6) / 1e9
            busbw = algbw * f
            row += f"  {fmt_time(t)}  {algbw:6.2f}  {busbw:6.2f}  {0:5d}"
        busbws.append(round(size / (float(fmt_time(t_oop[i])) * 1e-6) / 1e9 * f, 2))
        lines.append(row)
    lines += [
        "# Out of bounds values : 0 OK",
        f"# Avg bus bandwidth    : {np.mean(busbws):.4f} ",
        "#",
        "",
    ]
    return "\n".join(lines)


DEBUG_ALIGNED = """\
orion-n01:41022:41022 [0] NCCL INFO NCCL_SOCKET_IFNAME set by environment to fe0
orion-n01:41022:41022 [0] NCCL INFO NET/IB : Using [0]mlx5_0:1/RoCE [1]mlx5_1:1/RoCE [2]mlx5_2:1/RoCE [3]mlx5_3:1/RoCE [4]mlx5_4:1/RoCE [5]mlx5_5:1/RoCE [6]mlx5_6:1/RoCE [7]mlx5_7:1/RoCE ; OOB fe0:10.10.1.1<0>
orion-n01:41022:41090 [0] NCCL INFO comm 0x55d1c0 rank 0 nRanks 16 nNodes 2 localRanks 8 localRank 0
orion-n01:41022:41090 [0] NCCL INFO Channel 00/0 : 15[7] -> 0[0] [receive] via NET/IB/0/GDRDMA
orion-n01:41029:41097 [7] NCCL INFO Channel 00/0 : 7[7] -> 8[0] [send] via NET/IB/0(0)/GDRDMA
orion-n01:41026:41093 [4] NCCL INFO Channel 04/0 : 4[4] -> 12[4] [send] via NET/IB/4/GDRDMA
orion-n01:41026:41093 [4] NCCL INFO Channel 04/0 : 12[4] -> 4[4] [receive] via NET/IB/4/GDRDMA
"""

DEBUG_ALT = """\
orion-n01:52310:52310 [0] NCCL INFO NCCL_SOCKET_IFNAME set by environment to fe0
orion-n01:52310:52310 [0] NCCL INFO NCCL_IB_HCA set to mlx5_0,mlx5_1,mlx5_2,mlx5_3
orion-n01:52310:52310 [0] NCCL INFO NCCL_PXN_DISABLE set by environment to 1
orion-n01:52310:52310 [0] NCCL INFO NET/IB : Using [0]mlx5_0:1/RoCE [1]mlx5_1:1/RoCE [2]mlx5_2:1/RoCE [3]mlx5_3:1/RoCE ; OOB fe0:10.10.1.1<0>
orion-n01:52310:52377 [0] NCCL INFO comm 0x5612a0 rank 0 nRanks 16 nNodes 2 localRanks 8 localRank 0
orion-n01:52310:52377 [0] NCCL INFO Channel 00/0 : 15[7] -> 0[0] [receive] via NET/IB/0/GDRDMA
orion-n01:52314:52381 [4] NCCL INFO Channel 04/0 : 4[4] -> 12[4] [send] via NET/IB/2
orion-n01:52314:52381 [4] NCCL INFO Channel 04/0 : 12[4] -> 4[4] [receive] via NET/IB/2
orion-n01:52316:52383 [6] NCCL INFO Channel 06/0 : 6[6] -> 14[6] [send] via NET/IB/3
"""


def write_all(out: Path) -> None:
    """Write all lab data into ``out``."""
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    meta = {}
    for name, nodes, alpha, bw, ns, nl, desc in CONFIGS:
        n = nodes * 8
        t_oop = times_us(rng, n, alpha, bw, ns, nl)
        t_ip = times_us(rng, n, alpha, bw, ns, nl)
        text = render(name, nodes, t_oop, t_ip, rng)
        (out / f"{name}.log").write_text(text, encoding="utf-8", newline="\n")
        meta[name] = {"file": f"{name}.log", "nodes": nodes, "gpus_per_node": 8, "description": desc}
    with open(out / "configs.yaml", "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump({"collective": "all_reduce", "dtype": "float", "configs": meta}, fh, sort_keys=False)
    (out / "nccl_debug_c2_2node_aligned.txt").write_text(DEBUG_ALIGNED, encoding="utf-8", newline="\n")
    (out / "nccl_debug_c3_2node_alt_map.txt").write_text(DEBUG_ALT, encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = ap.parse_args()
    write_all(args.out)
    print(f"wrote nccl-tests style logs to {args.out}")


if __name__ == "__main__":
    main()
