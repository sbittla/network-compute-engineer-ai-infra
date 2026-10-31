"""Capstone C L2: port the benchmark harness to one GPU, profile it, and read NCCL's transport choice.

What it teaches (starter-kit README sections 5 and 8; manuscript Ch 11 collectives, Ch 14 profiling):
the L1 harness's discipline (warm-up, repetitions, percentiles, manifest, deterministic numerics)
carries over unchanged to a GPU. The data-parallel step proxy (per-rank matmul, then a ring
all-reduce of a gradient buffer) is ported to PyTorch on one device. Its result is checked against
the L1 numpy ``ring_allreduce``, and its phases are timed with CUDA events against the device's
FP32 and memory peaks. ``torch.profiler`` then classifies kernel time into GEMM, reduction and copy
work, as Nsight would. Finally a real one-rank ``torch.distributed`` process group is started with
``NCCL_DEBUG=INFO``, and its log is parsed with the L1 ``nccl_transport()``. It shows the same
"Using network Socket" signature as the baseline defect in ``data/nccl_debug_baseline.log``,
because this host has no RDMA device.

Not runnable on one GPU: multi-GPU NCCL collectives, weak scaling across 8 GPUs and multiple nodes,
GPUDirect RDMA, and Nsight Systems capture. Each is probed, and the probe result is recorded.

CPU fallback: the same harness on the CPU (fp32, bounded thread count), the CPU-operator profile, and
a gloo one-rank process group. The GPU-only invariants (FP32 peak, memory peak, NCCL transport) are
skipped.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXPERIMENT = {
    "id": "capstone-c-l2",
    "title": "Capstone C L2: the benchmark harness on one GPU, profiled, with NCCL transport evidence",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same ported harness (per-rank matmul + ring all-reduce) on the CPU in fp32, a CPU-operator "
                     "profile, and a gloo one-rank process group; multi-GPU NCCL and scaling are recorded as not runnable"),
}

PKG = Path(__file__).resolve().parents[2]
BUS_BITS = {"rtx 4060 laptop": 128, "rtx 4060": 128, "rtx 4070 laptop": 128, "rtx 4090": 384, "rtx 3090": 384}


def load_l1(name: str):
    for p in (PKG / "instructor" / "reference" / f"{name}.py", PKG / "starter-kit" / "starter" / f"{name}.py"):
        if p.is_file():
            spec = importlib.util.spec_from_file_location(f"l1_{name}", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, p.relative_to(PKG).as_posix()
    return None, None


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def peaks(env: dict) -> dict:
    """FP32 CUDA-core peak (SMs x 128 lanes x 2 FLOP x clocks.max.sm) and memory peak [VENDOR-SPEC]."""
    g = (env.get("gpus") or [{}])[0]
    sm, clk = env.get("gpu0", {}).get("sm_count"), num(g.get("clocks.max.sm"))
    name, mclk = (g.get("name") or "").lower(), num(g.get("clocks.max.memory"))
    bits = next((b for k, b in BUS_BITS.items() if k in name), None)
    return {"fp32_flops": sm * 256 * clk * 1e6 if sm and clk else None,
            "mem_bw": 2 * mclk * 1e6 * bits / 8 if bits and mclk else None}


# ---------------------------------------------------------------------------------- the ported harness
class _NoTimer:
    def __call__(self, cat):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class CatTimer:
    """Per-category time with CUDA events (GPU) or perf_counter (CPU): the fallback when no kernel trace exists."""

    def __init__(self, ctx):
        self.ctx, self.marks, self.cat = ctx, [], None

    def __call__(self, cat):
        self.cat = cat
        return self

    def __enter__(self):
        if self.ctx.is_gpu:
            e = self.ctx.torch.cuda.Event(enable_timing=True)
            e.record()
        else:
            e = time.perf_counter()
        self._start = (self.cat, e)
        return self

    def __exit__(self, *a):
        cat, e0 = self._start
        if self.ctx.is_gpu:
            e1 = self.ctx.torch.cuda.Event(enable_timing=True)
            e1.record()
        else:
            e1 = time.perf_counter()
        self.marks.append((cat, e0, e1))
        return False

    def totals_us(self) -> dict:
        self.ctx.sync()
        out: dict = {}
        for cat, e0, e1 in self.marks:
            dt = e0.elapsed_time(e1) * 1e3 if self.ctx.is_gpu else (e1 - e0) * 1e6
            out[cat] = out.get(cat, 0.0) + dt
        return out


def ring_allreduce_torch(bufs, tm=None):
    """The L1 ring algorithm on device tensors: reduce-scatter then all-gather over n chunks.
    Every 'send' is a device-memory copy/add between per-rank buffers. Returns elements sent per rank."""
    tm = tm or _NoTimer()
    n = len(bufs)
    length = bufs[0].numel()
    base, extra = divmod(length, n)
    bounds, start = [], 0
    for i in range(n):                       # same split as np.array_split
        stop = start + base + (1 if i < extra else 0)
        bounds.append((start, stop))
        start = stop
    sent = [0] * n
    for step in range(n - 1):
        msgs = [(r, (r - step) % n) for r in range(n)]
        with tm("copy"):
            data = [bufs[r][bounds[c][0]:bounds[c][1]].clone() for r, c in msgs]
        with tm("reduce_add"):
            for (r, c), d in zip(msgs, data):
                bufs[(r + 1) % n][bounds[c][0]:bounds[c][1]].add_(d)
                sent[r] += d.numel()
    for step in range(n - 1):
        msgs = [(r, (r + 1 - step) % n) for r in range(n)]
        with tm("copy"):
            data = [bufs[r][bounds[c][0]:bounds[c][1]].clone() for r, c in msgs]
            for (r, c), d in zip(msgs, data):
                bufs[(r + 1) % n][bounds[c][0]:bounds[c][1]].copy_(d)
                sent[r] += d.numel()
    return sent


def time_phase(ctx, fn):
    torch = ctx.torch
    if ctx.is_gpu:
        e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        e0.record()
        out = fn()
        e1.record()
        torch.cuda.synchronize()
        return e0.elapsed_time(e1) / 1000.0, out
    t0 = time.perf_counter()
    out = fn()
    return time.perf_counter() - t0, out


def harness(ctx, n_ranks: int, dim: int, grad_elems: int, warmup: int, reps: int, seed: int = 0) -> dict:
    torch = ctx.torch
    g = torch.Generator(device=ctx.device).manual_seed(seed)
    a = [torch.randn(dim, dim, device=ctx.device, generator=g) for _ in range(n_ranks)]
    b = [torch.randn(dim, dim, device=ctx.device, generator=g) for _ in range(n_ranks)]
    base = [torch.randn(grad_elems, device=ctx.device, generator=g) for _ in range(n_ranks)]
    comp, comm, total, sent = [], [], [], None
    for i in range(warmup + reps):
        grads = [x.clone() for x in base]
        ctx.sync()
        tc, _ = time_phase(ctx, lambda: [a[r] @ b[r] for r in range(n_ranks)])
        tm, sent = time_phase(ctx, lambda: ring_allreduce_torch(grads))
        if i >= warmup:
            comp.append(tc)
            comm.append(tm)
            total.append(tc + tm)
    ref_sum = torch.stack(base).sum(0)
    err = float(((grads[0] - ref_sum).abs().max() / ref_sum.abs().max()).item())
    return {"compute_s": comp, "comm_s": comm, "times_s": total, "sent_elems_per_rank": sent,
            "checksum": float(grads[0].double().sum().item()), "max_rel_err_vs_sum": err,
            "config": {"n_ranks": n_ranks, "dim": dim, "grad_elems": grad_elems, "warmup": warmup, "reps": reps, "seed": seed,
                       "dtype": "float32", "tf32": False}}


def crosscheck_l1(ctx, n_ranks: int) -> dict:
    """Same inputs through the L1 numpy ring_allreduce and the ported one: identical semantics and byte counts."""
    ref, src = load_l1("harness")
    if ref is None:
        return {"available": False}
    import numpy as np
    torch = ctx.torch
    rng = np.random.default_rng(3)
    bufs = [rng.standard_normal(1001) for _ in range(n_ranks)]           # a length that does not divide by n
    try:
        out_ref, sent_ref = ref.ring_allreduce([x.copy() for x in bufs])
    except NotImplementedError:
        return {"available": False, "why": "starter harness.ring_allreduce not implemented yet"}
    tb = [torch.tensor(x, dtype=torch.float64, device=ctx.device) for x in bufs]
    sent = ring_allreduce_torch(tb)
    dev = max(float(np.abs(t.cpu().numpy() - o).max()) for t, o in zip(tb, out_ref))
    return {"available": True, "source": src, "max_abs_diff": dev,
            "bytes_sent_match": [s * 8 for s in sent] == list(sent_ref), "sent_ref_bytes": list(sent_ref)}


def profile_step(ctx, n_ranks, dim, grad_elems) -> dict:
    """torch.profiler over 3 steps; kernels (GPU) or operators (CPU) classified like an Nsight summary."""
    torch = ctx.torch
    from torch.profiler import ProfilerActivity, profile
    a = torch.randn(dim, dim, device=ctx.device)
    grads = [torch.randn(grad_elems, device=ctx.device) for _ in range(n_ranks)]
    acts = [ProfilerActivity.CPU] + ([ProfilerActivity.CUDA] if ctx.is_gpu else [])

    def step():
        for _ in range(n_ranks):
            a @ a
        ring_allreduce_torch(grads)

    step()
    ctx.sync()
    t0 = time.perf_counter()
    with profile(activities=acts) as prof:
        for _ in range(3):
            step()
        ctx.sync()
    wall = time.perf_counter() - t0
    cats = {"gemm": 0.0, "reduce_add": 0.0, "copy": 0.0, "other": 0.0}
    for ev in prof.key_averages():
        name = ev.key.lower()
        if ctx.is_gpu:
            t = getattr(ev, "self_device_time_total", None)
            if t is None:
                t = getattr(ev, "self_cuda_time_total", 0)
            if t <= 0 or name.startswith("aten::") or name.startswith("cuda"):
                continue                                   # keep only kernels and memcpy/memset records
        else:
            if not name.startswith("aten::") or name in ("aten::empty", "aten::empty_like", "aten::slice", "aten::as_strided"):
                continue
            t = ev.self_cpu_time_total
        if any(k in name for k in ("gemm", "aten::mm", "cutlass", "sm80_xmma", "ampere_", "sm89", "matmul")):
            cats["gemm"] += t
        elif any(k in name for k in ("memcpy", "copy", "clone")):
            cats["copy"] += t
        elif any(k in name for k in ("add", "elementwise", "vectorized", "reduce")):
            cats["reduce_add"] += t
        else:
            cats["other"] += t
    basis = "CUDA kernel self time (torch.profiler/CUPTI)" if ctx.is_gpu else "CPU operator self time (torch.profiler)"
    kernel_trace = sum(cats.values()) > 0
    if ctx.is_gpu and not kernel_trace:
        # CUPTI kernel tracing is not available here (common under WSL2): time the same categories with CUDA events.
        tm = CatTimer(ctx)
        ctx.sync()
        t0 = time.perf_counter()
        for _ in range(3):
            with tm("gemm"):
                for _ in range(n_ranks):
                    a @ a
            ring_allreduce_torch(grads, tm)
        cats = {"gemm": 0.0, "reduce_add": 0.0, "copy": 0.0, "other": 0.0} | tm.totals_us()
        wall = time.perf_counter() - t0
        basis = "CUDA-event timed categories (CUPTI kernel trace unavailable in this container)"
    total = sum(cats.values()) or 1.0
    return {"basis": basis, "kernel_trace": kernel_trace, "us": cats,
            "fractions": {k: v / total for k, v in cats.items()}, "wall_s": wall, "busy_s": total / 1e6, "steps": 3}


DIST_SCRIPT = r"""
import json, sys, time, torch, torch.distributed as dist
backend, dev, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
dist.init_process_group(backend, init_method="tcp://127.0.0.1:29533", rank=0, world_size=1)
t = torch.ones(n, device=dev)
for _ in range(3): dist.all_reduce(t)
if dev == "cuda": torch.cuda.synchronize()
ts = []
for _ in range(5):
    t0 = time.perf_counter(); dist.all_reduce(t)
    if dev == "cuda": torch.cuda.synchronize()
    ts.append(time.perf_counter() - t0)
v = torch.cuda.nccl.version() if backend == "nccl" else None
print("RESULT " + json.dumps({"backend": backend, "times_s": ts, "nccl_version": ".".join(map(str, v)) if v else None}))
dist.destroy_process_group()
"""


def one_rank_process_group(ctx) -> dict:
    """A real torch.distributed group of world size 1 in a subprocess, with NCCL_DEBUG=INFO captured."""
    import torch.distributed as dist
    nccl = ctx.is_gpu and dist.is_available() and dist.is_nccl_available()
    backend = "nccl" if nccl else "gloo"
    env = dict(os.environ, NCCL_DEBUG="INFO", NCCL_DEBUG_SUBSYS="INIT,NET")
    p = subprocess.run([sys.executable, "-c", DIST_SCRIPT, backend, ctx.device, str(1 << 20)], capture_output=True,
                       text=True, timeout=120, env=env)
    log = p.stdout + p.stderr
    res = {"backend": backend, "nccl_available": bool(dist.is_nccl_available()), "returncode": p.returncode}
    for line in log.splitlines():
        if line.startswith("RESULT "):
            res.update(json.loads(line[7:]))
    res["log_excerpt"] = [ln for ln in log.splitlines() if "NCCL INFO" in ln and "Channel" not in ln and "Trees" not in ln][:20]
    if backend == "nccl":
        ana, src = load_l1("analysis")
        if ana is not None:
            try:
                res["nccl_transport"] = ana.nccl_transport(log)
                res["nccl_transport_source"] = src
                base = (PKG / "starter-kit" / "data" / "nccl_debug_baseline.log").read_text(encoding="utf-8")
                fixed = (PKG / "starter-kit" / "data" / "nccl_debug_ib_gdr.log").read_text(encoding="utf-8")
                res["supplied_logs"] = {"baseline": ana.nccl_transport(base), "ib_gdr": ana.nccl_transport(fixed)}
            except NotImplementedError:
                res["nccl_transport"] = None
    return res


def probes(ctx) -> dict:
    torch = ctx.torch
    ib = Path("/sys/class/infiniband")
    return {"cuda_device_count": torch.cuda.device_count() if ctx.is_gpu else 0,
            "rdma_devices": sorted(os.listdir(ib)) if ib.is_dir() else [], "dev_infiniband": Path("/dev/infiniband").exists(),
            "nsys": bool(shutil.which("nsys")), "nvidia_smi_topo": subprocess.run(["nvidia-smi", "topo", "-m"], capture_output=True,
                                                                               text=True).stdout.strip()[:600] if shutil.which("nvidia-smi") else ""}


def run(ctx) -> dict:
    torch = ctx.torch
    if ctx.is_gpu:
        torch.backends.cuda.matmul.allow_tf32 = False      # FP32 GEMM on CUDA cores: comparable with the FP32 peak
    else:
        torch.set_num_threads(min(8, os.cpu_count() or 1))
    n_ranks = 4
    dim = (2048 if ctx.quick else 4096) if ctx.is_gpu else (512 if ctx.quick else 1024)
    grad_elems = 8 * 2 ** 20 if ctx.is_gpu else 2 * 2 ** 20               # 32 MiB per rank on the GPU: beyond the L2 cache
    reps = ctx.reps(20)
    h = harness(ctx, n_ranks, dim, grad_elems, warmup=3, reps=reps)
    ref, src = load_l1("harness")
    summ = ref.summarize if ref is not None else None
    try:
        stats = {k: summ(h[k]) for k in ("times_s", "compute_s", "comm_s")}
        stats_src = src
    except (NotImplementedError, TypeError):
        import hwlab
        stats = {k: hwlab.summarize(h[k]) for k in ("times_s", "compute_s", "comm_s")}
        stats_src = "hwlab.summarize"
    flops = n_ranks * 2 * dim ** 3
    chunk = grad_elems / n_ranks
    # Device-memory traffic of the ring on one device: reduce-scatter clone(r+w) + add_(r+r+w); all-gather clone(r+w) + copy_(r+w).
    traffic = n_ranks * (n_ranks - 1) * chunk * 4 * (5 + 4)
    med_c, med_m = stats["compute_s"]["median"], stats["comm_s"]["median"]
    ctx.log(f"harness {n_ranks} ranks, dim {dim}, grad {grad_elems * 4 / 2 ** 20:.0f} MiB/rank: step {stats['times_s']['median'] * 1e3:.2f} ms "
            f"(compute {med_c * 1e3:.2f}, ring {med_m * 1e3:.2f}); {flops / med_c / 1e12:.2f} TFLOP/s, ring traffic {traffic / med_m / 1e9:.1f} GB/s")
    xc = crosscheck_l1(ctx, n_ranks)
    prof = profile_step(ctx, n_ranks, min(dim, 2048), grad_elems)
    pg = one_rank_process_group(ctx)
    ctx.log(f"process group: backend={pg['backend']} rc={pg['returncode']} transport={pg.get('nccl_transport')}")
    pr = probes(ctx)
    nr = [{"part": "multi-GPU NCCL collectives and weak scaling (8 GPUs per node, then 2+ nodes)",
           "probe": f"torch.cuda.device_count()={pr['cuda_device_count']}",
           "needs": ["8-GPU node with NVLink/NVSwitch", "2+ nodes with RDMA NICs"],
           "fallback": "simulated ranks on one device; one-rank process group for the NCCL log"},
          {"part": "GPUDirect RDMA / IB transport (NCCL 'Using network IB', '/GDRDMA')",
           "probe": f"/sys/class/infiniband={pr['rdma_devices'] or 'none'}, /dev/infiniband={pr['dev_infiniband']}",
           "needs": ["RDMA NIC (RoCEv2 or InfiniBand)", "nvidia_peermem or dma-buf", "rdma devices passed into the container"],
           "fallback": "the NCCL log of this host parsed with nccl_transport(): it shows the Socket fallback"},
          {"part": "Nsight Systems capture (nsys profile)", "probe": f"nsys on PATH={pr['nsys']}",
           "needs": ["Nsight Systems CLI in the image"], "fallback": "torch.profiler kernel classification"}]
    if ctx.is_gpu and not prof["kernel_trace"]:
        nr.append({"part": "CUDA kernel trace (torch.profiler CUDA activity via CUPTI)",
                   "probe": "torch.profiler returned no device-time records for CUDA kernels",
                   "needs": ["CUPTI kernel tracing (native Linux driver; often unavailable under WSL2)"],
                   "fallback": "the same categories timed with CUDA events around each operation group"})
    return {"metrics": {"step_ms_median": round(stats["times_s"]["median"] * 1e3, 3), "step_cv": round(stats["times_s"].get("cv", 0), 3),
                        "compute_tflops": round(flops / med_c / 1e12, 3), "ring_traffic_gbs": round(traffic / med_m / 1e9, 2),
                        "comm_fraction": round(med_m / (med_c + med_m), 3)},
            "harness": {k: v for k, v in h.items()}, "stats": stats, "stats_source": stats_src,
            "work": {"flops_per_step": flops, "ring_traffic_bytes": traffic, "bytes_sent_per_rank": [s * 4 for s in h["sent_elems_per_rank"]]},
            "l1_crosscheck": xc, "profile": prof, "process_group": pg, "probes": pr, "not_runnable_parts": nr,
            "notes": ["Harness: 3 warm-up steps, then timed steps; phases timed separately with CUDA events (GPU) or perf_counter (CPU).",
                      "Ranks are simulated on one device: the 'communication' phase is device-memory traffic, not NVLink or network. "
                      "It is the L1 algorithm, ported, not a measurement of any interconnect.",
                      "TF32 disabled so the GEMM is comparable with the FP32 CUDA-core peak."]}


def check(result: dict, env: dict) -> list[str]:
    fails = []
    h = result["harness"]
    if h["max_rel_err_vs_sum"] > 1e-5:
        fails.append(f"ported ring all-reduce differs from the plain sum by {h['max_rel_err_vs_sum']:.1e}: chunk bounds or step order are wrong")
    n = h["config"]["n_ranks"]
    expect = 2 * (n - 1) * h["config"]["grad_elems"]
    if sum(h["sent_elems_per_rank"]) != expect:
        fails.append(f"total elements sent {sum(h['sent_elems_per_rank'])} != 2(n-1) x buffer = {expect}: the ring moved the wrong amount")
    xc = result["l1_crosscheck"]
    if xc.get("available"):
        if xc["max_abs_diff"] > 1e-9:
            fails.append(f"ported ring disagrees with the L1 numpy ring_allreduce by {xc['max_abs_diff']:.1e} (float64)")
        if not xc["bytes_sent_match"]:
            fails.append("per-rank bytes sent differ from the L1 ring_allreduce accounting")
    if any(t <= 0 for t in h["times_s"]):
        fails.append("non-positive step time: check synchronisation")
    pf = result["profile"]
    if pf["fractions"]["gemm"] <= 0:
        fails.append("the profile attributes no time to GEMM: kernel classification is broken")
    if pf["busy_s"] > pf["wall_s"] * 1.10:
        fails.append(f"profiled busy time {pf['busy_s'] * 1e3:.1f} ms exceeds the wall time {pf['wall_s'] * 1e3:.1f} ms on one stream")
    pg = result["process_group"]
    if pg["returncode"] != 0 or not pg.get("times_s"):
        fails.append(f"the one-rank {pg['backend']} process group failed (rc={pg['returncode']}): see log_excerpt")
    if env["device"] == "cuda":
        pk = peaks(env)
        tf = result["work"]["flops_per_step"] / result["stats"]["compute_s"]["median"]
        if pk["fp32_flops"] and tf > 1.05 * pk["fp32_flops"]:
            fails.append(f"GEMM {tf / 1e12:.1f} TFLOP/s exceeds the FP32 peak {pk['fp32_flops'] / 1e12:.1f}: TF32 must have been on")
        bw = result["work"]["ring_traffic_bytes"] / result["stats"]["comm_s"]["median"]
        if pk["mem_bw"] and bw > 1.10 * pk["mem_bw"]:
            fails.append(f"ring traffic {bw / 1e9:.0f} GB/s exceeds the {pk['mem_bw'] / 1e9:.0f} GB/s memory peak: buffers are L2-resident "
                         "or the traffic model is wrong")
        tr = pg.get("nccl_transport")
        if pg["backend"] == "nccl" and tr:
            has_rdma = bool(result["probes"]["rdma_devices"])
            if tr["network"] == "IB" and not has_rdma:
                fails.append("NCCL reports IB but the probe found no RDMA device: the probe or the parser is wrong")
            if tr["network"] == "Socket" and has_rdma:
                fails.append("RDMA devices exist but NCCL fell back to Socket: pass /dev/infiniband into the container (the baseline defect)")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    c, s = result["harness"]["config"], result["stats"]
    L = ["## Ported harness (per-rank matmul + ring all-reduce, simulated ranks on one device)", "",
         f"{c['n_ranks']} ranks, matmul {c['dim']}x{c['dim']} fp32 (TF32 off), gradient buffer {c['grad_elems'] * 4 / 2 ** 20:.0f} MiB per rank, "
         f"{c['warmup']} warm-up + {c['reps']} timed steps. Statistics from `{result['stats_source']}`.", "",
         "| Phase | median (ms) | p95 (ms) | p99 (ms) | IQR (ms) | CV |", "|---|---|---|---|---|---|"]
    for k, label in (("times_s", "step"), ("compute_s", "compute (matmuls)"), ("comm_s", "ring all-reduce")):
        x = s[k]
        L.append(f"| {label} | {x['median'] * 1e3:.3f} | {x['p95'] * 1e3:.3f} | {x.get('p99', x['p95']) * 1e3:.3f} | "
                 f"{x['iqr'] * 1e3:.3f} | {x.get('cv', float('nan')):.3f} |")
    m = result["metrics"]
    L += ["", f"Compute **{m['compute_tflops']:.2f} TFLOP/s**; ring phase moves device memory at **{m['ring_traffic_gbs']:.0f} GB/s**; "
          f"communication is {m['comm_fraction'] * 100:.0f} % of the step (nothing overlaps here: one stream, phases in series)."]
    if gpu:
        pk = peaks(env)
        L.append(f"Bounds: FP32 CUDA-core peak {pk['fp32_flops'] / 1e12:.1f} TFLOP/s and memory {pk['mem_bw'] / 1e9:.0f} GB/s at max clocks "
                 "`[VENDOR-SPEC]` (SMs x 128 FP32 lanes x 2 x clocks.max.sm; GDDR6 2 x clocks.max.memory x bus width).")
    xc = result["l1_crosscheck"]
    if xc.get("available"):
        L += ["", f"L1 cross-check (`{xc['source']}` `ring_allreduce`, 1,001 float64 elements, {c['n_ranks']} ranks): max |difference| "
              f"{xc['max_abs_diff']:.1e}, per-rank bytes sent identical: **{xc['bytes_sent_match']}** {xc['sent_ref_bytes']}."]
    pf = result["profile"]
    L += ["", f"## Profile ({pf['basis']}, {pf['steps']} steps; in place of an nsys capture)", "",
          "| Category | time (ms) | share |", "|---|---|---|"]
    for k, v in pf["us"].items():
        L.append(f"| {k} | {v / 1e3:.2f} | {pf['fractions'][k] * 100:.0f} % |")
    pg = result["process_group"]
    L += ["", f"## torch.distributed, world size 1 ({pg['backend']})", "",
          f"all_reduce of 4 MiB, 5 timed calls: median {sorted(pg.get('times_s', [float('nan')]))[len(pg.get('times_s', [0])) // 2] * 1e3:.3f} ms"
          + (f"; NCCL {pg['nccl_version']}" if pg.get("nccl_version") else "") + "."]
    if pg.get("nccl_transport"):
        tr, sup = pg["nccl_transport"], pg.get("supplied_logs", {})
        L += ["", "| Log | network | GDR | IB devices | 'No device found' |", "|---|---|---|---|---|",
              f"| this host (measured) | {tr['network']} | {tr['gdr']} | {tr['ib_devices'] or '-'} | {tr['no_ib_device']} |"]
        for k, v in sup.items():
            L.append(f"| data/nccl_debug_{k}.log (supplied) | {v['network']} | {v['gdr']} | {len(v['ib_devices'])} | {v['no_ib_device']} |")
        L += ["", "Excerpt:", "", "```text"] + [ln.split("NCCL INFO", 1)[-1].strip() for ln in pg["log_excerpt"][:10]] + ["```"]
    elif gpu:
        L += ["", f"NCCL not available in this PyTorch build (is_nccl_available={pg['nccl_available']}); gloo used instead."]
    L += ["", "## Not runnable here", ""]
    for p in result["not_runnable_parts"]:
        L.append(f"- **{p['part']}**. Probe: {p['probe']}. Needs: {', '.join(p['needs'])}. Fallback: {p['fallback']}.")
    L += ["", "## What to conclude", "",
          "- The harness's numerics and byte accounting are identical to the L1 version. Only the device changed, so its timings "
          "can be trusted to mean what the L1 harness's meant.",
          "- The ring phase here is bounded by device memory bandwidth, not by any link. On a real node the same phase is bounded "
          "by NVLink (intra-node) or the NIC (inter-node), and NCCL overlaps it with backward compute. This proxy runs the "
          "phases in series, so the whole ring time is exposed."]
    if pg.get("nccl_transport"):
        L.append("- The NCCL log on this host has the **same signature as the supplied baseline**: libibverbs missing, then "
                 "'Using network Socket'. Without an RDMA device in the container, NCCL silently falls back to TCP. Check "
                 "this line before trusting any multi-node number.")
    if gpu:
        L.append("- This is a **laptop Ada GPU, not an H100 node**. Compare shapes, never absolute numbers, with the supplied ORION logs.")
    else:
        L.append("- _CPU fallback: no GPU was used. The FP32/memory-peak bounds and the NCCL transport check were skipped, and "
                 "gloo replaced NCCL._")
    return "\n".join(L)
