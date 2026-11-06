#!/usr/bin/env python3
"""Step 3: find the DataLoader configuration that keeps the GPU busy.

A synthetic image dataset whose samples cost real CPU time to produce (decode and augmentation stand-ins
in NumPy), feeding a small CNN training step on the GPU. The script measures:

  gpu_only   the training step on a batch already resident on the GPU: the ceiling (samples/s)
  cpu_batch  the time one process needs to produce one batch: the per-worker supply rate

then sweeps num_workers, pin_memory and prefetch_factor (each configuration three times; the median run is
kept). For each configuration it records samples/s, the
time the training loop waits for data, the GPU time of the training steps (CUDA events) as a fraction of
wall time ("GPU busy"), and nvidia-smi's utilization.gpu sampled every 200 ms during the run.

    python loader.py > loader.json
"""
from __future__ import annotations

import json
import math
import os
import statistics
import subprocess
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

H = W = 128
BATCH = 64
STEPS, WARMUP = 30, 5
AUG_PASSES = int(os.environ.get("CH13_AUG_PASSES", "6"))


class SyntheticImages(Dataset):
    """Each sample: generate a uint8 image (the 'decoded' bytes), then normalize and run AUG_PASSES of
    elementwise augmentation in float32 on the CPU. Deterministic per index."""

    def __len__(self):
        return 1_000_000

    def __getitem__(self, i):
        rng = np.random.default_rng(i)
        img = rng.integers(0, 256, size=(3, H, W), dtype=np.uint8)
        x = img.astype(np.float32) / 255.0
        for p in range(AUG_PASSES):
            x = np.tanh(x * 1.5 - 0.5) * 0.5 + 0.5
            if p % 2:
                x = x[:, :, ::-1]
        x = (x - 0.45) / 0.226
        return torch.from_numpy(np.ascontiguousarray(x)), int(i % 10)


def model():
    return nn.Sequential(
        nn.Conv2d(3, 64, 3, 2, 1), nn.ReLU(), nn.Conv2d(64, 128, 3, 2, 1), nn.ReLU(),
        nn.Conv2d(128, 256, 3, 2, 1), nn.ReLU(), nn.Conv2d(256, 256, 3, 1, 1), nn.ReLU(),
        nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(256, 10)).cuda()


class Trainer:
    def __init__(self):
        self.m = model()
        self.opt = torch.optim.SGD(self.m.parameters(), lr=0.01)
        self.loss = nn.CrossEntropyLoss()

    def step(self, x, y):
        self.opt.zero_grad(set_to_none=True)
        out = self.m(x)
        self.loss(out, y).backward()
        self.opt.step()


class UtilSampler:
    def __init__(self):
        self.p = subprocess.Popen(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits", "-lms", "200"],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

    def stop(self):
        self.p.terminate()
        out, _ = self.p.communicate(timeout=10)
        vals = [int(v) for v in out.split() if v.strip().isdigit()]
        return vals


def gpu_only(tr: Trainer) -> dict:
    x = torch.randn(BATCH, 3, H, W, device="cuda")
    y = torch.randint(0, 10, (BATCH,), device="cuda")
    for _ in range(WARMUP):
        tr.step(x, y)
    torch.cuda.synchronize()
    s, e = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    s.record()
    for _ in range(STEPS):
        tr.step(x, y)
    e.record()
    torch.cuda.synchronize()
    ms = s.elapsed_time(e) / STEPS
    return {"step_ms": round(ms, 3), "samples_per_s": round(BATCH / ms * 1e3, 1)}


def cpu_batch() -> dict:
    ds = SyntheticImages()
    t = []
    for b in range(3):
        t0 = time.perf_counter()
        for i in range(BATCH):
            ds[b * BATCH + i]
        t.append((time.perf_counter() - t0) * 1e3)
    ms = statistics.median(t)
    return {"batch_ms": round(ms, 2), "samples_per_s_per_worker": round(BATCH / ms * 1e3, 1)}


def run_config(tr: Trainer, workers: int, pin: bool, prefetch: int | None) -> dict:
    kw = {"num_workers": workers, "pin_memory": pin, "batch_size": BATCH, "shuffle": False}
    if workers > 0:
        kw["prefetch_factor"] = prefetch
    dl = DataLoader(SyntheticImages(), **kw)
    it = iter(dl)
    for _ in range(WARMUP):
        x, y = next(it)
        tr.step(x.cuda(non_blocking=True), y.cuda(non_blocking=True))
    torch.cuda.synchronize()
    util = UtilSampler()
    waits, evs = [], []
    t0 = time.perf_counter()
    for _ in range(STEPS):
        tw = time.perf_counter()
        x, y = next(it)
        waits.append(time.perf_counter() - tw)
        a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        x = x.cuda(non_blocking=True)
        y = y.cuda(non_blocking=True)
        a.record()
        tr.step(x, y)
        b.record()
        evs.append((a, b))
    torch.cuda.synchronize()
    wall = time.perf_counter() - t0
    samples = util.stop()
    del it, dl
    gpu_ms = sum(a.elapsed_time(b) for a, b in evs)
    return {"workers": workers, "pin_memory": pin, "prefetch_factor": prefetch,
            "samples_per_s": round(STEPS * BATCH / wall, 1), "step_ms": round(wall / STEPS * 1e3, 2),
            "data_wait_ms_per_step": round(sum(waits) / STEPS * 1e3, 2),
            "data_wait_fraction": round(sum(waits) / wall, 3),
            "gpu_busy_fraction": round(gpu_ms / 1e3 / wall, 3),
            "nvidia_smi_util_mean": round(statistics.mean(samples), 1) if samples else None,
            "nvidia_smi_util_samples": samples}


def run_config_median(tr: Trainer, workers: int, pin: bool, prefetch: int | None, reps: int = 3) -> dict:
    """Run one configuration `reps` times (fresh DataLoader each time) and keep the median run by samples/s:
    other processes on a shared host make single runs of a CPU-bound pipeline noisy."""
    runs = sorted((run_config(tr, workers, pin, prefetch) for _ in range(reps)), key=lambda r: r["samples_per_s"])
    med = runs[len(runs) // 2]
    med["samples_per_s_all_reps"] = [r["samples_per_s"] for r in runs]
    return med


def main() -> int:
    torch.manual_seed(0)
    torch.backends.cudnn.benchmark = True
    tr = Trainer()
    res = {"gpu": torch.cuda.get_device_name(0), "torch": torch.__version__, "cpus": os.cpu_count(),
           "batch": BATCH, "image": [3, H, W], "aug_passes": AUG_PASSES, "steps": STEPS, "warmup": WARMUP,
           "batch_mib_float32": round(BATCH * 3 * H * W * 4 / 2**20, 2)}
    res["gpu_only"] = gpu_only(tr)
    res["cpu_batch"] = cpu_batch()
    res["workers_needed_estimate"] = math.ceil(res["cpu_batch"]["batch_ms"] / res["gpu_only"]["step_ms"])
    grid = [(w, False, 2) for w in (0, 1, 2, 4, 8, 12)] + [(w, True, 2) for w in (0, 2, 4, 8, 12)] + \
           [(4, True, pf) for pf in (1, 4, 8)]
    res["configs"] = [run_config_median(tr, w, p, pf if w > 0 else None) for w, p, pf in grid]
    best = max(c["samples_per_s"] for c in res["configs"])
    enough = [c for c in res["configs"] if c["samples_per_s"] >= 0.95 * best]
    cheapest = min(enough, key=lambda c: (c["workers"], c["prefetch_factor"] or 0, c["pin_memory"]))
    res["best_samples_per_s"] = best
    res["cheapest_within_5pct_of_best"] = {k: cheapest[k] for k in ("workers", "pin_memory", "prefetch_factor", "samples_per_s", "gpu_busy_fraction")}
    res["best_over_ceiling"] = round(best / res["gpu_only"]["samples_per_s"], 3)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
