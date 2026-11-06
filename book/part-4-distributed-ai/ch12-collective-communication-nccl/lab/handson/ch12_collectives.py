#!/usr/bin/env python3
"""Chapter 12 hands-on worker: time torch.distributed collectives across processes, nccl-tests style.

Run under torchrun, one process per rank. CPU ranks use gloo; a CUDA rank uses NCCL.

Size convention (the one nccl-tests uses): S is the size of the *whole* vector, so for all_reduce and
broadcast S is each rank's buffer, for all_gather S is the gathered output (each rank contributes S/n)
and for reduce_scatter S is the input (each rank keeps S/n). Time is the mean over `iters` back-to-back
calls, and the reported time is the slowest rank's. algbw = S / time; busbw = algbw x factor, with
factor 2(n-1)/n for all_reduce, (n-1)/n for all_gather and reduce_scatter, 1 for broadcast.

Besides the library collectives, two hand-written all-reduces built from send/recv let you compare
algorithms the backend does not let you choose: `ring_allreduce` (n-1 reduce-scatter steps plus n-1
all-gather steps, each moving S/n) and `tree_allreduce` (a binomial-tree reduce to rank 0 and a
broadcast back, 2 log2(n) steps each moving S). `pingpong` (2 ranks) measures one-way point-to-point
time, the alpha and beta of the Hockney model.

Rank 0 appends one JSON object per (op, size) to --out and prints an nccl-tests-like table.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import sys
import time

import torch
import torch.distributed as dist

FACTOR = {"all_reduce": lambda n: 2 * (n - 1) / n, "ring_allreduce": lambda n: 2 * (n - 1) / n,
          "tree_allreduce": lambda n: 2 * (n - 1) / n, "all_gather": lambda n: (n - 1) / n,
          "reduce_scatter": lambda n: (n - 1) / n, "broadcast": lambda n: 1.0, "pingpong": lambda n: 1.0}


def ring_allreduce(buf: torch.Tensor, rank: int, n: int, tmp: torch.Tensor) -> None:
    chunks = buf.chunk(n)
    right, left = (rank + 1) % n, (rank - 1) % n
    for step in range(n - 1):                         # reduce-scatter: rank r ends owning chunk r+1
        si, ri = (rank - step) % n, (rank - step - 1) % n
        req = dist.isend(chunks[si], right)
        dist.recv(tmp, left)
        chunks[ri].add_(tmp)
        req.wait()
    for step in range(n - 1):                         # all-gather: circulate the reduced chunks
        si, ri = (rank - step + 1) % n, (rank - step) % n
        req = dist.isend(chunks[si], right)
        dist.recv(chunks[ri], left)
        req.wait()


def tree_allreduce(buf: torch.Tensor, rank: int, n: int, tmp: torch.Tensor) -> None:
    d = 1
    while d < n:                                      # binomial-tree reduce to rank 0
        if rank % (2 * d) == d:
            dist.send(buf, rank - d)
        elif rank % (2 * d) == 0 and rank + d < n:
            dist.recv(tmp, rank + d)
            buf.add_(tmp)
        d *= 2
    d //= 2
    while d >= 1:                                     # binomial-tree broadcast from rank 0
        if rank % (2 * d) == 0 and rank + d < n:
            dist.send(buf, rank + d)
        elif rank % (2 * d) == d:
            dist.recv(buf, rank - d)
        d //= 2


class Case:
    """Buffers and one call of one collective at one size."""

    def __init__(self, op: str, nominal: int, rank: int, n: int, device: torch.device):
        self.op, self.rank, self.n = op, rank, n
        elems = max(1, nominal // 4)
        if op in ("all_gather", "reduce_scatter", "ring_allreduce"):
            elems = max(n, math.ceil(elems / n) * n)      # the whole vector must split into n chunks
        self.count, self.bytes = elems, elems * 4
        z = lambda k: torch.zeros(k, dtype=torch.float32, device=device)  # noqa: E731
        if op == "all_gather":
            self.inp, self.out = z(elems // n), z(elems)
        elif op == "reduce_scatter":
            self.inp, self.out = z(elems), z(elems // n)
        else:
            self.inp = z(elems)
            self.out = self.inp
        self.tmp = z(elems // n if op == "ring_allreduce" else elems) if op in ("ring_allreduce", "tree_allreduce", "pingpong") else None

    def run(self) -> None:
        op, r, n = self.op, self.rank, self.n
        if op == "all_reduce":
            dist.all_reduce(self.inp)
        elif op == "all_gather":
            dist.all_gather_into_tensor(self.out, self.inp)
        elif op == "reduce_scatter":
            dist.reduce_scatter_tensor(self.out, self.inp)
        elif op == "broadcast":
            dist.broadcast(self.inp, src=0)
        elif op == "ring_allreduce":
            ring_allreduce(self.inp, r, n, self.tmp)
        elif op == "tree_allreduce":
            tree_allreduce(self.inp, r, n, self.tmp)
        elif op == "pingpong":
            if r == 0:
                dist.send(self.inp, 1)
                dist.recv(self.tmp, 1)
            elif r == 1:
                dist.recv(self.tmp, 0)
                dist.send(self.tmp, 0)

    def validate(self) -> int:
        """Run once on known data and count wrong elements on this rank (nccl-tests' #wrong)."""
        op, r, n = self.op, self.rank, self.n
        if op == "pingpong":
            return 0
        if op == "all_gather":
            self.inp.fill_(r + 1)
            self.run()
            expect = torch.arange(1, n + 1, dtype=torch.float32, device=self.out.device).repeat_interleave(self.count // n)
            return int((self.out != expect).sum())
        if op == "reduce_scatter":
            chunk = self.count // n
            self.inp.copy_((r + 1) * torch.arange(1, n + 1, dtype=torch.float32, device=self.inp.device).repeat_interleave(chunk))
            self.run()
            return int((self.out != (r + 1) * n * (n + 1) / 2).sum())
        if op == "broadcast":
            self.inp.fill_(r + 1)
            self.run()
            return int((self.inp != 1).sum())
        self.inp.fill_(r + 1)                          # all-reduce flavours: sum of 1..n everywhere
        self.run()
        return int((self.inp != n * (n + 1) / 2).sum())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ops", default="all_reduce,all_gather,reduce_scatter,broadcast")
    ap.add_argument("--min-bytes", type=int, default=4)
    ap.add_argument("--max-bytes", type=int, default=64 * 2**20)
    ap.add_argument("--step-factor", type=int, default=2)
    ap.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    ap.add_argument("--same-gpu", action="store_true", help="put every rank on GPU 0 (NCCL is expected to refuse)")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--min-iters", type=int, default=5)
    ap.add_argument("--max-iters", type=int, default=1000)
    ap.add_argument("--target-s", type=float, default=0.2, help="aim for this much timed work per size")
    ap.add_argument("--out", default="", help="rank-0 JSONL output (appended)")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    torch.set_num_threads(a.threads)
    if a.device == "cuda":
        torch.cuda.set_device(0 if a.same_gpu else int(os.environ.get("LOCAL_RANK", "0")))
        device, backend = torch.device("cuda"), "nccl"
    else:
        device, backend = torch.device("cpu"), "gloo"
    t0 = time.perf_counter()
    dist.init_process_group(backend, timeout=datetime.timedelta(seconds=300))
    rank, n = dist.get_rank(), dist.get_world_size()
    probe = torch.zeros(1, device=device)
    dist.all_reduce(probe)                             # NCCL creates its communicator lazily: include it
    if device.type == "cuda":
        torch.cuda.synchronize()
    init_s = time.perf_counter() - t0
    sync = (lambda: torch.cuda.synchronize()) if device.type == "cuda" else (lambda: None)

    sizes, s = [], a.min_bytes
    while s <= a.max_bytes:
        sizes.append(s)
        s *= a.step_factor
    rows = []
    for op in [o.strip() for o in a.ops.split(",") if o.strip()]:
        if op == "pingpong" and n < 2:
            continue
        seen = set()
        for nominal in sizes:
            c = Case(op, nominal, rank, n, device)
            if c.bytes in seen:                        # tiny sizes round up to n elements: test each size once
                continue
            seen.add(c.bytes)
            for _ in range(a.warmup):
                c.run()
            sync()
            dist.barrier()
            tw = time.perf_counter()
            c.run()
            sync()
            est = torch.tensor([time.perf_counter() - tw], device=device)
            dist.all_reduce(est, op=dist.ReduceOp.MAX)
            iters = int(min(a.max_iters, max(a.min_iters, a.target_s / max(float(est), 1e-7))))
            dist.barrier()
            t1 = time.perf_counter()
            for _ in range(iters):
                c.run()
            sync()
            el = torch.tensor([(time.perf_counter() - t1) / iters], device=device)
            dist.all_reduce(el, op=dist.ReduceOp.MAX)  # the slowest rank defines the collective's time
            t_us = float(el) * 1e6
            if op == "pingpong":
                t_us /= 2                              # one-way time from the round trip
            wrong = torch.tensor([c.validate()], device=device)
            dist.all_reduce(wrong)
            alg = c.bytes / (t_us * 1e-6) / 1e9
            rec = {"op": op, "n": n, "bytes": c.bytes, "nominal_bytes": nominal, "count": c.count, "iters": iters,
                   "time_us": t_us, "algbw_gbs": alg, "busbw_gbs": alg * FACTOR[op](n), "wrong": int(wrong),
                   "backend": backend, "device": device.type, "tag": a.tag}
            rows.append(rec)
            del c
    if rank == 0:
        if a.out:
            with open(a.out, "a", encoding="utf-8") as f:
                f.write(json.dumps({"op": "_init", "n": n, "init_s": init_s, "backend": backend,
                                    "device": device.type, "torch": torch.__version__, "tag": a.tag}) + "\n")
                for r in rows:
                    f.write(json.dumps(r) + "\n")
        print(f"# {backend} on {device.type}, nranks {n}, init + first collective {init_s * 1e3:.1f} ms, tag {a.tag}")
        print(f"# {'op':>15s} {'size':>10s} {'count':>10s} {'iters':>6s} {'time(us)':>11s} {'algbw':>8s} {'busbw':>8s} #wrong")
        for r in rows:
            print(f"  {r['op']:>15s} {r['bytes']:10d} {r['count']:10d} {r['iters']:6d} {r['time_us']:11.2f} "
                  f"{r['algbw_gbs']:8.3f} {r['busbw_gbs']:8.3f} {r['wrong']:6d}")
    dist.destroy_process_group()
    return 0


if __name__ == "__main__":
    sys.exit(main())
