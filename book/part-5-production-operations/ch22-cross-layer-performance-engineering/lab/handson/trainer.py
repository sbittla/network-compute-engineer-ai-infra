#!/usr/bin/env python3
"""Ch 22 hands-on: a training loop whose input batches come over the network from a data server.

Pipeline: DataLoader workers fetch raw batches (uint8) over HTTP from dataserver.py, decode them on the CPU
(a fixed amount of single-threaded numpy work per batch, standing in for decompression and augmentation), and
the loop copies each batch to the GPU and runs forward, backward and a fused AdamW step of an MLP.

Knobs (the healthy configuration is the default):
  --workers N      DataLoader worker processes (0 = decode in the training process itself)
  --inflight K     fetches each worker keeps in flight (1 = fetch, decode, fetch, ...)
  --inject-sync    a debug hook that copies every block's output to the host and summarizes it with numpy,
                   plus loss.item() every step
  --decode-rounds  CPU work per batch (run.sh calibrates it to about twice the GPU step time)
  --no-data        skip the pipeline (one batch reused on the GPU): measures the GPU-only step time

Evidence it records (one JSON line on stdout): the workload's own clock first (step time; exposed data wait,
the GPU's idle gap between steps measured with CUDA events; and the time the loop blocks in next(iterator),
which overlaps GPU work still queued from the previous step), then per-batch fetch and decode wall time, decode CPU time and run-queue
delay (from /proc/thread-self/schedstat: time a runnable thread waited for a CPU), the main thread's CPU
use and run-queue delay, nvidia-smi GPU-Util, CPU affinity, and with --profile the CUDA synchronize calls per
step from torch.profiler.
"""
from __future__ import annotations

import argparse
import collections
import http.client
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import numpy as np
import torch

os.environ.setdefault("OMP_NUM_THREADS", "1")


def schedstat_ns(path: str = "/proc/thread-self/schedstat") -> tuple[int, int]:
    """(on-CPU ns, run-queue wait ns) for the calling thread."""
    try:
        with open(path) as f:
            run, wait, _ = f.read().split()
        return int(run), int(wait)
    except (OSError, ValueError):
        return 0, 0


class Fetcher:
    """A persistent HTTP/1.1 connection per thread."""

    def __init__(self, url: str):
        u = urlparse(url)
        self.host, self.port = u.hostname, u.port or 80
        self.local = threading.local()

    def get(self, i: int) -> bytes:
        for attempt in range(3):
            conn = getattr(self.local, "conn", None)
            if conn is None:
                conn = self.local.conn = http.client.HTTPConnection(self.host, self.port, timeout=30)
            try:
                conn.request("GET", f"/batch/{i}")
                r = conn.getresponse()
                body = r.read()
                if r.status != 200:
                    raise OSError(f"HTTP {r.status}")
                return body
            except (OSError, http.client.HTTPException):
                conn.close()
                self.local.conn = None
                if attempt == 2:
                    raise
        raise OSError("unreachable")


def decode(raw: bytes, tokens: int, d: int, rounds: int) -> np.ndarray:
    x = np.frombuffer(raw, dtype=np.uint8)[: tokens * d].astype(np.float32)
    x *= 1.0 / 255.0
    for _ in range(rounds):                      # stand-in for decompression / augmentation: pure CPU work
        np.tanh(x, out=x)
        x *= 1.7
    return x.reshape(tokens, d)


class RemoteBatches(torch.utils.data.IterableDataset):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def __iter__(self):
        a = self.a
        info = torch.utils.data.get_worker_info()
        wid, nw = (info.id, info.num_workers) if info else (0, 1)
        torch.set_num_threads(1)
        fetcher = Fetcher(a.server)
        idx = iter(range(wid, 1 << 30, nw))

        def timed_fetch(i):
            t0 = time.perf_counter()
            raw = fetcher.get(i)
            return raw, (time.perf_counter() - t0) * 1e3

        pool = ThreadPoolExecutor(max_workers=a.inflight) if a.inflight > 1 else None
        ahead: collections.deque = collections.deque()
        while True:
            if pool:
                while len(ahead) < a.inflight:
                    ahead.append(pool.submit(timed_fetch, next(idx)))
                t0 = time.perf_counter()
                raw, fetch_ms = ahead.popleft().result()
                wait_ms = (time.perf_counter() - t0) * 1e3          # how long the worker waited for the network
            else:
                raw, fetch_ms = timed_fetch(next(idx))
                wait_ms = fetch_ms
            c0, (r0, q0), w0 = time.thread_time(), schedstat_ns(), time.perf_counter()
            x = decode(raw, a.tokens, a.d, a.decode_rounds)
            c1, (r1, q1), w1 = time.thread_time(), schedstat_ns(), time.perf_counter()
            meta = torch.tensor([fetch_ms, wait_ms, (w1 - w0) * 1e3, (c1 - c0) * 1e3, (q1 - q0) / 1e6, float(os.getpid())],
                                dtype=torch.float64)
            yield torch.from_numpy(x), meta


class Model(torch.nn.Module):
    def __init__(self, d: int, blocks: int):
        super().__init__()
        self.layers = torch.nn.ModuleList()
        for _ in range(blocks):
            self.layers.append(torch.nn.Sequential(torch.nn.Linear(d, 4 * d), torch.nn.GELU(), torch.nn.Linear(4 * d, d)))

    def forward(self, x):
        for layer in self.layers:
            x = x + layer(x)
        return x


def gpu_util_sampler(path: str):
    return subprocess.Popen(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits", "-lms", "100",
                             "-i", "0"], stdout=open(path, "w"), stderr=subprocess.DEVNULL)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--server", default="http://10.22.0.2:8222")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--inflight", type=int, default=1)
    ap.add_argument("--inject-sync", action="store_true")
    ap.add_argument("--decode-rounds", type=int, default=8)
    ap.add_argument("--tokens", type=int, default=4096)
    ap.add_argument("--d", type=int, default=1024)
    ap.add_argument("--blocks", type=int, default=4)
    ap.add_argument("--warmup", type=int, default=15)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--log-every", type=int, default=20)
    ap.add_argument("--no-data", action="store_true")
    ap.add_argument("--profile", action="store_true", help="also count CUDA syncs per step with torch.profiler")
    ap.add_argument("--sync-debug", action="store_true", help="print set_sync_debug_mode warnings for one step")
    ap.add_argument("--util-file", default="")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    torch.set_num_threads(1)
    torch.manual_seed(22)
    model = Model(a.d, a.blocks).cuda()
    opt = torch.optim.AdamW(model.parameters(), lr=1e-5, fused=True)
    if a.inject_sync:
        def debug_stat(mod, inp, out):            # "just a debug statistic": .cpu() waits for the GPU,
            np.abs(out.detach().float().cpu().numpy()).max()   # then the GPU idles while the CPU summarizes
        for layer in model.layers:
            layer.register_forward_hook(debug_stat)

    if a.no_data:
        fixed = torch.randn(a.tokens, a.d).pin_memory()
        meta0 = torch.zeros(6, dtype=torch.float64)

        def gen():
            while True:
                yield fixed, meta0
        it = gen()
    else:
        ds = RemoteBatches(a)
        loader = torch.utils.data.DataLoader(ds, batch_size=None, num_workers=a.workers, pin_memory=True,
                                             prefetch_factor=2 if a.workers > 0 else None)
        it = iter(loader)

    def train_step(x, log: bool):
        x = x.cuda(non_blocking=True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = model(x).float().pow(2).mean()
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)
        if a.inject_sync or log:
            return loss.item()
        return None

    waits, steps_ms, metas, gaps = [], [], [], []
    prev_end = None
    main_tid = threading.get_native_id()
    sampler = None
    t_window = None
    n_total = a.warmup + a.steps
    t_prev = time.perf_counter()
    for i in range(n_total):
        if i == a.warmup:
            torch.cuda.synchronize()
            if a.util_file:
                sampler = gpu_util_sampler(a.util_file)
            t_window = time.perf_counter()
            c_main0, (r_main0, q_main0) = time.thread_time(), schedstat_ns(f"/proc/self/task/{main_tid}/schedstat")
            t_prev = t_window
        t0 = time.perf_counter()
        x, meta = next(it)
        t1 = time.perf_counter()
        ev_start = torch.cuda.Event(enable_timing=True)
        ev_start.record()
        train_step(x, log=(i % a.log_every == 0))
        ev_end = torch.cuda.Event(enable_timing=True)
        ev_end.record()
        if i > a.warmup:          # GPU idle between the previous step's last kernel and this step's first
            gaps.append((prev_end, ev_start))
        prev_end = ev_end
        if i >= a.warmup:
            waits.append((t1 - t0) * 1e3)
            metas.append(meta.tolist())
            now = time.perf_counter()
            steps_ms.append((now - t_prev) * 1e3)
            t_prev = now
    torch.cuda.synchronize()
    t_end = time.perf_counter()
    c_main1, (r_main1, q_main1) = time.thread_time(), schedstat_ns(f"/proc/self/task/{main_tid}/schedstat")
    if sampler:
        sampler.terminate()
        sampler.wait(timeout=10)
    window_ms = (t_end - t_window) * 1e3
    idle_ms = [e0.elapsed_time(e1) for e0, e1 in gaps]
    m = np.array(metas) if metas else np.zeros((1, 6))
    util = []
    if a.util_file and os.path.exists(a.util_file):
        for line in open(a.util_file):
            try:
                util.append(float(line.strip()))
            except ValueError:
                pass
    out = {
        "label": a.label, "pid": os.getpid(), "config": {"workers": a.workers, "inflight": a.inflight, "inject_sync": a.inject_sync,
                                     "decode_rounds": a.decode_rounds, "tokens": a.tokens, "d": a.d, "blocks": a.blocks,
                                     "no_data": a.no_data, "affinity": sorted(os.sched_getaffinity(0)),
                                     "server": None if a.no_data else a.server},
        "steps": a.steps, "warmup": a.warmup,
        "step_ms": window_ms / a.steps,                       # throughput-based: window / steps
        "step_ms_median": statistics.median(steps_ms),
        # Time blocked in next(iterator) overlaps GPU work still queued from the previous step; the exposed
        # part is the GPU's idle gap between steps (CUDA events), scaled from steps-1 gaps to the window.
        "data_block_ms_median": statistics.median(waits), "data_block_share": sum(waits) / window_ms,
        "data_wait_ms_median": statistics.median(idle_ms) if idle_ms else 0.0,
        "data_wait_share": (sum(idle_ms) * a.steps / max(len(idle_ms), 1)) / window_ms,
        "fetch_ms_median": float(np.median(m[:, 0])), "fetch_wait_ms_median": float(np.median(m[:, 1])),
        "decode_ms_median": float(np.median(m[:, 2])), "decode_cpu_ms_median": float(np.median(m[:, 3])),
        "decode_runqueue_ms_median": float(np.median(m[:, 4])),
        "decode_runqueue_share": float(m[:, 4].sum() / max(m[:, 2].sum(), 1e-9)),
        "main_cpu_share": (c_main1 - c_main0) * 1e3 / window_ms,
        "main_runqueue_share": (q_main1 - q_main0) / 1e6 / window_ms,
        "gpu_util_median": statistics.median(util) if util else None, "gpu_util_samples": len(util),
        "loader_pids": sorted({int(p) for p in m[:, 5]}),
    }
    if a.profile:
        from torch.profiler import ProfilerActivity, profile
        names = []
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
            for i in range(3):
                x, _ = next(it)
                train_step(x, log=False)
            torch.cuda.synchronize()
        names = [e.name for e in prof.events()]
        out["profile_syncs_per_step"] = (sum(n in ("cudaStreamSynchronize", "cudaDeviceSynchronize") for n in names) - 1) / 3
        out["profile_item_per_step"] = sum(n == "aten::_local_scalar_dense" for n in names) / 3
    if a.sync_debug:
        import warnings
        x, _ = next(it)
        torch.cuda.synchronize()
        torch.cuda.set_sync_debug_mode("warn")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            train_step(x, log=False)
        torch.cuda.set_sync_debug_mode("default")
        out["sync_debug_warnings"] = len(w)
        for x in w[:3]:
            print(f"WARNING {x.filename}:{x.lineno}: {x.message}", file=sys.stderr)
    print(json.dumps(out))
    sys.stdout.flush()
    sys.stderr.flush()
    if not a.no_data and a.workers > 0:
        it._shutdown_workers()                    # stop the loader workers before exiting
    os._exit(0)                                   # skip interpreter teardown (worker threads may sit in recv)


if __name__ == "__main__":
    sys.exit(main())
