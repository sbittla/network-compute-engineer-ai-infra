#!/usr/bin/env python3
"""Chapter 11 hands-on worker: a small data-parallel training job for torchrun.

One process per rank. CPU ranks use the gloo backend; a CUDA rank uses NCCL. The model is a stack of
square Linear+GELU layers ((depth + 1) x (width^2 + width) parameters, 9.45 M at the defaults, 37.8 MB of FP32
gradients), trained with SGD + momentum on a synthetic regression task whose data depend only on
(seed, step, micro-batch, rank), so a resumed run sees exactly the data an uninterrupted run would.

Rank 0 appends one JSON object per event to --event-log:
  start  (attempt, resume step, world size, settings)        step  (step, wall time, step seconds, loss)
  ckpt   (step, seconds to write + fsync + barrier)           done  (peak RSS, final loss, DDP buckets)
Fault events (kill, hang, peer_error) from any rank go to --fault-log.

Examples (see run.sh for the full experiment list):
  torchrun --standalone --nproc-per-node=4 ch11_ddp.py --steps 30 --event-log /tmp/x.jsonl
  torchrun --standalone --nproc-per-node=4 --max-restarts=3 ch11_ddp.py --steps 144 \
      --ckpt-dir /tmp/ck --ckpt-every 12 --fault kill --fault-steps 20,50 --fault-rank 2 ...
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import resource
import signal
import sys
import time
from contextlib import nullcontext
from pathlib import Path

import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP


def jlog(path: str | None, rec: dict) -> None:
    """Append one JSON line with a single O_APPEND write, with SIGTERM blocked so a handler cannot split it."""
    if not path:
        return
    data = (json.dumps(rec) + "\n").encode()
    old = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
    try:
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, old)


def build_model(width: int, depth: int) -> nn.Module:
    layers: list[nn.Module] = []
    for _ in range(depth):
        layers += [nn.Linear(width, width), nn.GELU()]
    layers.append(nn.Linear(width, width))
    return nn.Sequential(*layers)


def batch(seed: int, step: int, micro: int, rank: int, mb: int, width: int, teacher: torch.Tensor,
          device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    g = torch.Generator().manual_seed(((seed * 1_000_003 + step) * 1_009 + micro) * 131 + rank)
    x = torch.randn(mb, width, generator=g)
    y = torch.tanh(x @ teacher)
    return x.to(device), y.to(device)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=5, help="steps excluded from the timing summary")
    ap.add_argument("--micro-batch", type=int, default=32, help="samples per rank per micro-batch")
    ap.add_argument("--accum", type=int, default=1, help="micro-batches per step (no_sync on all but the last)")
    ap.add_argument("--bucket-cap-mb", type=float, default=None,
                    help="DDP bucket_cap_mb; omit for PyTorch's default (25 MiB, plus a 1 MiB first bucket)")
    ap.add_argument("--no-comm", action="store_true", help="run every micro-batch under no_sync: compute only")
    ap.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    ap.add_argument("--threads", type=int, default=1, help="torch intra-op threads per rank (CPU)")
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--lr", type=float, default=0.02)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--pg-timeout", type=float, default=60.0, help="init_process_group timeout, seconds")
    ap.add_argument("--ckpt-dir", default="")
    ap.add_argument("--ckpt-every", type=int, default=0, help="checkpoint every K steps (0 = never)")
    ap.add_argument("--fault", choices=["none", "kill", "hang"], default="none")
    ap.add_argument("--fault-rank", type=int, default=1)
    ap.add_argument("--fault-steps", default="", help="comma-separated steps at which the fault fires once each")
    ap.add_argument("--event-log", default="", help="rank-0 JSONL event log (appended)")
    ap.add_argument("--fault-log", default="", help="JSONL fault log, any rank (appended)")
    ap.add_argument("--tag", default="", help="free text copied into the start event")
    a = ap.parse_args()

    rank = int(os.environ.get("RANK", "0"))
    world = int(os.environ.get("WORLD_SIZE", "1"))
    attempt = int(os.environ.get("TORCHELASTIC_RESTART_COUNT", "0"))
    torch.set_num_threads(a.threads)
    if a.device == "cuda":
        torch.cuda.set_device(int(os.environ.get("LOCAL_RANK", "0")))
        device, backend = torch.device("cuda"), "nccl"
    else:
        device, backend = torch.device("cpu"), "gloo"
    def on_sigterm(signum, frame):  # torchrun's agent stops surviving workers with SIGTERM
        jlog(a.fault_log, {"ev": "sigterm", "rank": rank, "t": time.time(), "attempt": attempt})
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        os.kill(os.getpid(), signal.SIGTERM)
    signal.signal(signal.SIGTERM, on_sigterm)
    t_init = time.time()
    dist.init_process_group(backend, timeout=datetime.timedelta(seconds=a.pg_timeout))
    init_s = time.time() - t_init

    torch.manual_seed(a.seed)                      # identical initial weights on every rank
    model = build_model(a.width, a.depth).to(device)
    teacher = torch.randn(a.width, a.width, generator=torch.Generator().manual_seed(a.seed + 7)) / a.width ** 0.5
    ddp = DDP(model, bucket_cap_mb=a.bucket_cap_mb)
    opt = torch.optim.SGD(ddp.parameters(), lr=a.lr, momentum=0.9)
    n_params = sum(p.numel() for p in model.parameters())

    start_step = 0
    ckpt = Path(a.ckpt_dir) / "ckpt.pt" if a.ckpt_dir else None
    if ckpt is not None:
        ckpt.parent.mkdir(parents=True, exist_ok=True)
    if ckpt is not None and ckpt.exists():
        state = torch.load(ckpt, map_location="cpu", weights_only=True)
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["opt"])
        start_step = int(state["step"])
    fault_steps = {int(s) for s in a.fault_steps.split(",") if s.strip()}
    marker_dir = Path(a.ckpt_dir or "/tmp") / "fault-markers"

    if rank == 0:
        jlog(a.event_log, {"ev": "start", "t": time.time(), "attempt": attempt, "resume_step": start_step,
                     "world": world, "backend": backend, "device": a.device, "params": n_params,
                     "grad_mb": n_params * 4 / 1e6, "bucket_cap_mb": a.bucket_cap_mb, "accum": a.accum,
                     "micro_batch": a.micro_batch, "no_comm": a.no_comm, "threads": a.threads,
                     "pg_timeout_s": a.pg_timeout, "init_s": round(init_s, 4), "tag": a.tag})

    loss_val = float("nan")
    step = start_step
    try:
        while step < a.steps:
            s = step + 1                                       # the step being executed (1-based)
            if a.fault != "none" and rank == a.fault_rank and s in fault_steps:
                marker_dir.mkdir(parents=True, exist_ok=True)
                m = marker_dir / f"{a.fault}-{s}"
                if not m.exists():                             # fire once, not again after the restart
                    m.touch()
                    jlog(a.fault_log, {"ev": a.fault, "rank": rank, "step": s, "t": time.time(),
                                       "attempt": attempt, "pg_timeout_s": a.pg_timeout})
                    if a.fault == "kill":
                        os.kill(os.getpid(), signal.SIGKILL)
                    else:
                        time.sleep(10 ** 6)                    # stop participating; peers block
            if a.device == "cuda":
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            opt.zero_grad(set_to_none=True)
            for micro in range(a.accum):
                sync = (micro == a.accum - 1) and not a.no_comm
                with (nullcontext() if sync else ddp.no_sync()):
                    x, y = batch(a.seed, s, micro, rank, a.micro_batch, a.width, teacher, device)
                    loss = nn.functional.mse_loss(ddp(x), y) / a.accum
                    loss.backward()
            opt.step()
            if a.device == "cuda":
                torch.cuda.synchronize()
            dt = time.perf_counter() - t0
            loss_val = float(loss.detach()) * a.accum
            step = s
            if rank == 0:
                jlog(a.event_log, {"ev": "step", "step": s, "t": time.time(), "dt": dt, "loss": loss_val,
                             "attempt": attempt})
            if ckpt is not None and a.ckpt_every and s % a.ckpt_every == 0:
                tc = time.perf_counter()
                if rank == 0:
                    tmp = ckpt.with_suffix(".tmp")
                    with open(tmp, "wb") as f:
                        torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "step": s}, f)
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(tmp, ckpt)                      # atomic: a crash never leaves half a file
                dist.barrier()
                if rank == 0:
                    jlog(a.event_log, {"ev": "ckpt", "step": s, "t": time.time(), "dt": time.perf_counter() - tc})
    except Exception as e:  # noqa: BLE001 - record how a peer learns about the failure, then fail
        jlog(a.fault_log, {"ev": "peer_error", "rank": rank, "step": step + 1, "t": time.time(),
                           "attempt": attempt, "type": type(e).__name__, "err": str(e)[:400]})
        raise

    try:   # DDP's own record of the buckets it built after its iteration-1 rebuild (private API; best effort)
        buckets = {k: v for k, v in ddp._get_ddp_logging_data().items() if "bucket" in k}
    except Exception as e:  # noqa: BLE001
        buckets = {"unavailable": str(e)[:100]}
    rss = torch.tensor([resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0])   # MiB
    gathered = [torch.zeros(1) for _ in range(world)]
    dist.all_gather(gathered, rss) if backend == "gloo" else None
    # parameter checksum across replicas: DDP keeps every replica identical
    csum = torch.tensor([sum(float(p.detach().double().sum()) for p in model.parameters())])
    cs = [torch.zeros(1, dtype=torch.float64) for _ in range(world)]
    if backend == "gloo":
        dist.all_gather(cs, csum.double())
    if rank == 0:
        jlog(a.event_log, {"ev": "done", "t": time.time(), "attempt": attempt, "final_step": step, "final_loss": loss_val,
                     "peak_rss_mib": [round(float(r), 1) for r in gathered] if backend == "gloo" else
                     [round(float(rss), 1)],
                     "cuda_peak_mib": round(torch.cuda.max_memory_allocated() / 2**20, 1) if a.device == "cuda" else None,
                     "param_checksums": [float(c) for c in cs] if backend == "gloo" else [float(csum)],
                     "ddp_buckets": buckets})
    dist.destroy_process_group()
    return 0


if __name__ == "__main__":
    sys.exit(main())
