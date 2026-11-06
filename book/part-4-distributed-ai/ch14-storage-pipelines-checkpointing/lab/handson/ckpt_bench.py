#!/usr/bin/env python3
"""Chapter 14 hands-on lab, step 4: checkpoint save and load, synchronous vs asynchronous, on one GPU.

    python ckpt_bench.py --out results/<run-id> [--dir /var/tmp/ch14-handson/ckpt] [--reps 5]

Three save methods on the same model and optimizer state, each one warm-up plus --reps timed runs:
  sync       torch.distributed.checkpoint.save (FileSystemWriter, sync_files=True: includes fsync)
  dcp_async  torch.distributed.checkpoint.async_save (stages to CPU, persists in a background thread)
  thread     our own: snapshot to reused pinned host buffers, then torch.save + fsync in a thread
Records blocking time (call -> training may continue), completion time (call -> durable), training
step time before / during / after the persist, bytes on disk, and dcp.load time with a cold and a
warm page cache. Checks that an async checkpoint equals the state at the call. Writes
<out>/raw/ckpt_bench.json. Run under the GPU lock (run.sh does this).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import statistics
import sys
import threading
import time
from pathlib import Path

import torch
import torch.distributed as dist
import torch.distributed.checkpoint as dcp
from torch.distributed.checkpoint.state_dict import get_state_dict
from torch.utils._pytree import tree_map

GiB = 2**30


def meminfo() -> dict[str, int]:
    return {k: int(v.split()[0]) * 1024 for k, v in
            (line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())}


def evict(path: Path) -> str:
    """Make the next read come from the disk: drop the page cache (root) or fadvise each file."""
    os.sync()
    try:
        Path("/proc/sys/vm/drop_caches").write_text("1\n")
        return "drop_caches"
    except OSError:
        for p in path.rglob("*"):
            if p.is_file():
                fd = os.open(p, os.O_RDONLY)
                os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                os.close(fd)
        return "posix_fadvise(DONTNEED)"


def du(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def fsync_dir(path: Path) -> None:
    for p in path.rglob("*"):
        if p.is_file():
            fd = os.open(p, os.O_RDONLY)
            os.fsync(fd)
            os.close(fd)
    fd = os.open(path, os.O_RDONLY)
    os.fsync(fd)
    os.close(fd)


class Trainer:
    """An MLP sized so FP32 weights + Adam moments (12 B/param) stay well inside 7 GB of host RAM."""

    def __init__(self, d: int, layers: int, batch: int):
        torch.manual_seed(0)
        blocks = []
        for _ in range(layers):
            blocks += [torch.nn.Linear(d, 4 * d), torch.nn.GELU(), torch.nn.Linear(4 * d, d)]
        self.model = torch.nn.Sequential(*blocks).cuda()
        # fused=True keeps Adam's step counters on the GPU, so async staging copies them too
        # (with CPU scalar steps, DCP stages them by reference: see lab/l2 and Section 14.10).
        self.opt = torch.optim.Adam(self.model.parameters(), lr=1e-4, fused=True)
        g = torch.Generator(device="cuda").manual_seed(1)
        self.x = torch.randn(batch, d, device="cuda", generator=g)
        self.y = torch.randn(batch, d, device="cuda", generator=g)
        self.params = sum(p.numel() for p in self.model.parameters())

    def step(self) -> float:
        t0 = time.perf_counter()
        self.opt.zero_grad(set_to_none=True)
        loss = torch.nn.functional.mse_loss(self.model(self.x), self.y)
        loss.backward()
        self.opt.step()
        torch.cuda.synchronize()
        return time.perf_counter() - t0

    def state(self) -> dict:
        msd, osd = get_state_dict(self.model, self.opt)
        return {"model": msd, "optim": osd}


def tensors(sd) -> list[torch.Tensor]:
    out: list[torch.Tensor] = []
    tree_map(lambda v: out.append(v) if isinstance(v, torch.Tensor) else None, sd)
    return out


def state_bytes(sd) -> int:
    return sum(t.numel() * t.element_size() for t in tensors(sd))


def steps_while(tr: Trainer, busy) -> list[float]:
    times = []
    while busy():
        times.append(tr.step())
    return times


def save_sync(tr: Trainer, path: Path) -> dict:
    sd = tr.state()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    dcp.save(sd, storage_writer=dcp.FileSystemWriter(str(path), sync_files=True))
    fsync_dir(path)
    t = time.perf_counter() - t0
    return {"blocking_s": t, "completion_s": t, "during_ms": []}


def save_dcp_async(tr: Trainer, path: Path) -> dict:
    sd = tr.state()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    fut = dcp.async_save(sd, storage_writer=dcp.FileSystemWriter(str(path), sync_files=True))
    t_block = time.perf_counter() - t0
    during = steps_while(tr, lambda: not fut.done())
    fut.result()
    fsync_dir(path)
    return {"blocking_s": t_block, "completion_s": time.perf_counter() - t0,
            "during_ms": [x * 1e3 for x in during]}


class PinnedSnapshot:
    """Our own async checkpoint: D2H into pinned buffers allocated once, torch.save + fsync in a thread."""

    def __init__(self, sd):
        self.bufs = tree_map(lambda v: torch.empty(v.shape, dtype=v.dtype, pin_memory=True)
                             if isinstance(v, torch.Tensor) else v, sd)

    def snapshot(self, sd) -> None:
        src, dst = tensors(sd), tensors(self.bufs)
        for s, d in zip(src, dst):
            d.copy_(s, non_blocking=True)
        torch.cuda.synchronize()


def save_thread(tr: Trainer, path: Path, snap: PinnedSnapshot) -> dict:
    sd = tr.state()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    snap.snapshot(sd)
    t_block = time.perf_counter() - t0
    path.mkdir(parents=True, exist_ok=True)
    err: list[BaseException] = []

    def persist():
        try:
            tmp = path / "state.pt.tmp"
            with open(tmp, "wb") as f:
                torch.save(snap.bufs, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path / "state.pt")        # atomic commit (Section 14.10)
            fd = os.open(path, os.O_RDONLY)
            os.fsync(fd)
            os.close(fd)
        except BaseException as e:  # noqa: BLE001
            err.append(e)

    th = threading.Thread(target=persist, name="ch14-persist")
    th.start()
    during = steps_while(tr, th.is_alive)
    th.join()
    if err:
        raise err[0]
    return {"blocking_s": t_block, "completion_s": time.perf_counter() - t0,
            "during_ms": [x * 1e3 for x in during], "snapshot_gbs": state_bytes(sd) / t_block / 1e9}


def med(xs):
    return statistics.median(xs) if xs else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--dir", type=Path, default=Path(os.environ.get("CH14_EXT4_DIR", "/var/tmp/ch14-handson")) / "ckpt")
    ap.add_argument("--d", type=int, default=1024)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--reps", type=int, default=5)
    a = ap.parse_args()
    if not torch.cuda.is_available():
        sys.exit("no CUDA device: the checkpoint step needs the GPU")
    raw = a.out / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    # A one-rank gloo group: async_save in torch 2.5 wants an initialized group with a CPU backend.
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    dist.init_process_group("gloo", init_method=f"tcp://127.0.0.1:{port}", rank=0, world_size=1)

    tr = Trainer(a.d, a.layers, a.batch)
    tr.step()                                   # creates Adam state
    sd0 = tr.state()
    sbytes = state_bytes(sd0)
    m = meminfo()
    need = 4 * sbytes + GiB
    res: dict = {"state_bytes": sbytes, "params": tr.params, "model": f"MLP d={a.d} layers={a.layers} (FP32 + Adam)",
                 "batch": a.batch, "reps": a.reps, "dir": str(a.dir), "mem_available_bytes": m["MemAvailable"],
                 "swap_used_bytes_start": m["SwapTotal"] - m["SwapFree"], "torch": torch.__version__,
                 "gpu": torch.cuda.get_device_name(0)}
    if m["MemAvailable"] < need:
        res["status"] = "not-runnable"
        res["reason"] = (f"MemAvailable {m['MemAvailable'] / GiB:.2f} GiB < 4 x state + 1 GiB = {need / GiB:.2f} GiB: "
                         "the host would page and the timings would measure swap, not checkpointing")
        (raw / "ckpt_bench.json").write_text(json.dumps(res, indent=1))
        print(res["reason"])
        return 2
    del sd0
    print(f"state {sbytes / 1e9:.3f} GB ({tr.params / 1e6:.1f} M params), target {a.dir}", flush=True)

    shutil.rmtree(a.dir, ignore_errors=True)
    a.dir.mkdir(parents=True)
    base = [tr.step() * 1e3 for _ in range(30)][5:]
    res["step_ms_baseline"] = base
    snap = PinnedSnapshot(tr.state())
    methods = {"sync": lambda p: save_sync(tr, p), "dcp_async": lambda p: save_dcp_async(tr, p),
               "thread": lambda p: save_thread(tr, p, snap)}
    runs: dict[str, list] = {k: [] for k in methods}
    for rep in range(0, a.reps + 1):            # rep 0 is the warm-up; methods interleaved per rep
        for name, fn in methods.items():
            p = a.dir / f"{name}-{rep}"
            before = [tr.step() * 1e3 for _ in range(8)]
            r = fn(p)
            after = [tr.step() * 1e3 for _ in range(8)]
            r.update(rep=rep, warmup=rep == 0, bytes_on_disk=du(p), files=len([x for x in p.rglob("*") if x.is_file()]),
                     before_ms=before, after_ms=after, swap_used_bytes=meminfo()["SwapTotal"] - meminfo()["SwapFree"])
            runs[name].append(r)
            print(f"  {name:9s} rep {rep}: blocking {r['blocking_s']:.3f} s, completion {r['completion_s']:.3f} s, "
                  f"{r['bytes_on_disk'] / 1e9:.3f} GB, {len(r['during_ms'])} steps during persist", flush=True)
            if rep < a.reps:
                shutil.rmtree(p)
    res["saves"] = runs

    # Load: dcp.load in place into the live state dict, cold (page cache evicted) and warm.
    loads = []
    src = a.dir / f"sync-{a.reps}"
    for rep in range(a.reps):
        for cache in ("cold", "warm"):
            how = evict(src) if cache == "cold" else "none"
            sd = tr.state()
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            dcp.load(sd, storage_reader=dcp.FileSystemReader(str(src)))
            torch.cuda.synchronize()
            t = time.perf_counter() - t0
            loads.append({"rep": rep, "cache": cache, "evict": how, "load_s": t, "gbs": sbytes / t / 1e9})
            print(f"  dcp.load {cache}: {t:.3f} s ({sbytes / t / 1e9:.2f} GB/s)", flush=True)
    res["loads"] = loads

    # Consistency: does an async checkpoint equal the state at the moment of the call?
    sd = tr.state()
    ref = tree_map(lambda v: v.detach().clone() if isinstance(v, torch.Tensor) else v, sd)
    cpath = a.dir / "consistency"
    fut = dcp.async_save(sd, storage_writer=dcp.FileSystemWriter(str(cpath), sync_files=True))
    n_during = len(steps_while(tr, lambda: not fut.done()))
    fut.result()
    tgt = tree_map(lambda v: torch.zeros_like(v) if isinstance(v, torch.Tensor) else v, tr.state())
    dcp.load(tgt, storage_reader=dcp.FileSystemReader(str(cpath)))
    diff = [i for i, (x, y) in enumerate(zip(tensors(ref), tensors(tgt))) if not torch.equal(x, y)]
    live_moved = not all(torch.equal(x, y) for x, y in zip(tensors(ref), tensors(tr.state())))
    res["consistency"] = {"tensors": len(tensors(ref)), "differ_from_state_at_call": len(diff),
                          "steps_during_persist": n_during, "live_state_changed_meanwhile": live_moved}
    print(f"  consistency: {len(diff)} of {len(tensors(ref))} tensors differ; {n_during} steps ran meanwhile; "
          f"live state changed: {live_moved}", flush=True)
    del ref, tgt, snap

    res["mem_available_bytes_end"] = meminfo()["MemAvailable"]
    res["swap_used_bytes_end"] = meminfo()["SwapTotal"] - meminfo()["SwapFree"]
    res["gpu_mem_peak_bytes"] = torch.cuda.max_memory_allocated()
    res["status"] = "ran"
    (raw / "ckpt_bench.json").write_text(json.dumps(res, indent=1))
    shutil.rmtree(a.dir, ignore_errors=True)
    dist.destroy_process_group()
    print(f"checkpoint bench done: medians sync {med([r['completion_s'] for r in runs['sync'][1:]]):.3f} s, "
          f"dcp_async blocking {med([r['blocking_s'] for r in runs['dcp_async'][1:]]):.3f} s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
