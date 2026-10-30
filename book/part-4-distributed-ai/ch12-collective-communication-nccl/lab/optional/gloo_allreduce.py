#!/usr/bin/env python3
"""OPTIONAL (L1, requires PyTorch): CPU-only all-reduce sweep with the gloo backend.

Spawns ``--world`` processes on this machine, runs ``torch.distributed.all_reduce`` over a range of
message sizes, and prints the result in the same column layout as nccl-tests ``all_reduce_perf`` so
that your ``parse_nccl_log`` can read it. ``check.py`` never runs this script (PyTorch may be absent).

What it teaches: the PyTorch Distributed API (init_process_group, ranks, world size, collectives,
barriers), warm-up versus timed iterations, and how the latency- and bandwidth-dominated regions look
on *your* machine. What it cannot teach: anything about NCCL, GPUs, NVLink, RDMA, or a fabric — gloo
over loopback measures CPU memory copies and the TCP stack. Label every number it produces
[MEASURED] on "laptop, gloo, loopback" and never compare it with GPU results.

Usage:
    python optional/gloo_allreduce.py --world 4 --max-bytes 67108864 > data_local/gloo_w4.log
"""
from __future__ import annotations

import argparse
import os
import socket
import time

import torch
import torch.distributed as dist
import torch.multiprocessing as mp


def worker(rank: int, world: int, sizes: list[int], warmup: int, iters: int, port: int) -> None:
    """One rank: initialize gloo, sweep sizes, print an nccl-tests-style table on rank 0."""
    os.environ["MASTER_ADDR"] = "127.0.0.1"
    os.environ["MASTER_PORT"] = str(port)
    dist.init_process_group(backend="gloo", rank=rank, world_size=world)
    host = socket.gethostname()
    f = 2 * (world - 1) / world
    rows = []
    for size in sizes:
        n = max(1, size // 4)
        buf = torch.zeros(n, dtype=torch.float32)
        for _ in range(warmup):
            dist.all_reduce(buf)
        dist.barrier()
        t0 = time.perf_counter()
        for _ in range(iters):
            dist.all_reduce(buf)
        dt = torch.tensor([(time.perf_counter() - t0) / iters])
        dist.all_reduce(dt, op=dist.ReduceOp.MAX)          # slowest rank defines the collective
        rows.append((n * 4, n, dt.item() * 1e6))
    if rank == 0:
        print(f"# nThread 1 nGpus 1 minBytes {sizes[0]} maxBytes {sizes[-1]} step: 2(factor) "
              f"warmup iters: {warmup} iters: {iters} agg iters: 1 validation: 0 graph: 0")
        print("#\n# Using devices")
        for r in range(world):
            print(f"#  Rank {r:2d} Group  0 Pid {os.getpid():6d} on {host:>8s} device  {r} [cpu] gloo")
        print("#\n#       size         count      type   redop    root     time   algbw   busbw #wrong"
              "     time   algbw   busbw #wrong")
        for size, count, t_us in rows:
            alg = size / (t_us * 1e-6) / 1e9
            cols = f"  {t_us:7.2f}  {alg:6.2f}  {alg * f:6.2f}  {0:5d}"
            print(f"{size:12d}  {count:12d}     float     sum      -1{cols}{cols}")
        print("# gloo all_reduce is in-place only; in-place columns repeat the out-of-place values.")
    dist.destroy_process_group()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--world", type=int, default=4, help="number of local processes (ranks)")
    ap.add_argument("--min-bytes", type=int, default=8)
    ap.add_argument("--max-bytes", type=int, default=64 * 2**20)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--iters", type=int, default=20)
    ap.add_argument("--port", type=int, default=29512)
    args = ap.parse_args()
    sizes, s = [], args.min_bytes
    while s <= args.max_bytes:
        sizes.append(s)
        s *= 2
    mp.spawn(worker, args=(args.world, sizes, args.warmup, args.iters, args.port), nprocs=args.world, join=True)


if __name__ == "__main__":
    main()
