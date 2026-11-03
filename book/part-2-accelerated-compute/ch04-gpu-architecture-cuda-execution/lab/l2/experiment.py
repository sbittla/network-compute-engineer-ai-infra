"""Ch 4 L2: capture a real training step, export it in the lab's trace schema, classify its kernels and
run the lab's own trace analysis on it; then apply the fixes and measure before/after.

What it teaches (Sections 4.5, 4.6, 4.10-4.12): a step's time is GPU work plus the gaps between it, and
the gaps have causes you can read from a timeline: pageable host-to-device copies, host syncs (``.item()``
per layer), and launch-bound bursts of tiny kernels (an un-fused optimizer). The "baseline" step has all
three on purpose; the "fixed" step pins and prefetches the batch, drops the per-layer ``.item()`` and
uses the fused AdamW. Both steps are captured, written as ``gpu_trace.csv`` / ``cuda_api_trace.csv`` /
``nvtx_ranges.csv`` / ``device.json`` and analysed by ``solutions/lab/trace_analysis.py:analyze()``.
The uninstrumented step times are then compared (median of >= 5 runs, Chapter 6 protocol).

The capture. ``torch.profiler`` (CUPTI) records the CPU side for real here (aten ops and the CUDA runtime
calls: launches, copies, syncs), but under WSL2 it records **no GPU activity** (probed below: 0 device
events). So GPU-side intervals come from an instrumenting tracer: a ``TorchDispatchMode`` that brackets
every kernel-launching aten op with a pair of CUDA events on the current stream, converts them to the
host clock through a reference event recorded right after a synchronize, and records the op's dispatch
interval as its API call. FLOPs come from ``torch.utils.flop_counter``'s registry (GEMMs) or one per
output element; bytes are the compulsory traffic of the op's tensors (a lower bound). What the tracer
cannot see is the launch configuration (grid, block, registers, shared memory): occupancy is therefore
not computed and LOW_OCCUPANCY cannot fire; that part needs CUPTI kernel records or Nsight Compute.
The tracer adds ~10-30 us of host time per op, which inflates launch-bound gaps: the gap *causes* are
right, their sizes are upper bounds, and the step-time comparison is measured without it.

CPU fallback: torch.profiler captures the same two steps on the CPU (aten ops by self time, classified
into GEMM / elementwise / reduction / optimizer / copy), the uninstrumented before/after step times are
measured, and the lab's analyze() runs on the shipped SIMULATED trace so the pipeline is still
exercised; the GPU-only invariants (PCIe bound, sync gaps, GPU roofs) are skipped and the report says so.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch04-l2",
    "title": "Lab 4 L2: capture, classify and analyse a real training step (before and after the fixes)",
    "evidence": "MEASURED",
    "cpu_fallback": ("torch.profiler capture of the same baseline and fixed steps on the CPU, aten ops classified by self "
                     "time, uninstrumented before/after step times, and the lab's analyze() on the shipped simulated trace"),
}

PKG = Path(__file__).resolve().parents[2]
PCIE_GBPS_PER_LANE = {1: 0.25, 2: 0.5, 3: 0.985, 4: 1.969, 5: 3.938, 6: 7.563}
BF16_FLOP_PER_CLK_SM = {(8, 9): 512, (8, 6): 512, (8, 0): 2048, (9, 0): 4096}   # NVIDIA architecture whitepapers
BUS_BITS = {"rtx 4060 laptop": 128, "rtx 4060": 128, "rtx 4070 laptop": 128, "rtx 4090": 384, "rtx 3090": 384}
# Per-SM limits by compute capability, CUDA C++ Programming Guide, "Technical Specifications per Compute Capability".
CC_LIMITS = {(8, 9): {"max_warps_per_sm": 48, "max_threads_per_sm": 1536, "max_blocks_per_sm": 24,
                      "smem_per_sm_bytes": 102400, "max_smem_per_block_bytes": 101376},
             (8, 6): {"max_warps_per_sm": 48, "max_threads_per_sm": 1536, "max_blocks_per_sm": 16,
                      "smem_per_sm_bytes": 102400, "max_smem_per_block_bytes": 101376},
             (9, 0): {"max_warps_per_sm": 64, "max_threads_per_sm": 2048, "max_blocks_per_sm": 32,
                      "smem_per_sm_bytes": 233472, "max_smem_per_block_bytes": 232448}}
NO_KERNEL_OPS = {"view", "_unsafe_view", "t", "transpose", "as_strided", "expand", "detach", "alias", "permute",
                 "unsqueeze", "squeeze", "slice", "select", "empty", "empty_like", "empty_strided", "new_empty",
                 "new_empty_strided", "split", "unbind", "_reshape_alias", "lift_fresh", "split_with_sizes",
                 "_to_copy_meta", "set_", "resize_", "is_same_size", "_has_compatible_shallow_copy_type"}
CATEGORY = [("gemm", ("mm", "addmm", "bmm", "baddbmm", "matmul", "linear", "_scaled_mm")),
            ("optimizer", ("_fused_adamw", "_fused_adam", "_foreach_")),
            ("reduction", ("sum", "mean", "norm", "amax", "max", "min", "var", "std")),
            ("sync", ("_local_scalar_dense",))]


def load_solution():
    # Reference solution when present (instructor tree); the learner's starter/ in the student release.
    path = PKG / "solutions" / "lab" / "trace_analysis.py"
    if not path.is_file():
        path = PKG / "lab" / "starter" / "trace_analysis.py"
    spec = importlib.util.spec_from_file_location("ch04_trace_analysis", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def category(op: str, kind: str) -> str:
    if kind == "memcpy":
        return "memcpy"
    base = op.split(".")[0]
    for cat, keys in CATEGORY:
        if base in keys or any(base.startswith(k) for k in keys if k.endswith("_")):
            return cat
    if base in ("copy_", "_to_copy"):
        return "cast/copy"
    return "elementwise"


# ------------------------------------------------------------------ the training step
def build(ctx, fixed: bool):
    torch = ctx.torch
    gpu = ctx.is_gpu
    dev = "cuda" if gpu else "cpu"
    d, blocks = (1024, 4) if gpu else (256, 4)
    tokens = (2048 if ctx.quick else 4096) if gpu else (256 if ctx.quick else 512)
    torch.manual_seed(4)
    layers = []
    for _ in range(blocks):
        layers += [torch.nn.Linear(d, 4 * d), torch.nn.GELU(), torch.nn.Linear(4 * d, d)]
    model = torch.nn.Sequential(*layers).to(dev)
    if fixed:
        opt = torch.optim.AdamW(model.parameters(), lr=1e-4, fused=True) if gpu else \
            torch.optim.AdamW(model.parameters(), lr=1e-4, foreach=True)
    else:
        opt = torch.optim.AdamW(model.parameters(), lr=1e-4, foreach=False)
        for m in model:
            if isinstance(m, torch.nn.Linear):   # the debug hook from Section 4.14: one host sync per layer
                m.register_forward_hook(lambda mod, inp, out: _debug_stat(out))
    host = torch.randn(tokens, d)
    if fixed and gpu:
        host = host.pin_memory()
    copy_stream = torch.cuda.Stream() if gpu else None
    state = {"prefetched": None}

    def step(rf=None):
        rec = rf or (lambda name: _null())
        with rec("h2d_batch"):
            if fixed and gpu:
                cur = torch.cuda.current_stream()
                if state["prefetched"] is None:
                    with torch.cuda.stream(copy_stream):
                        state["prefetched"] = host.to(dev, non_blocking=True)
                cur.wait_stream(copy_stream)          # the batch for this step was copied during the previous one
                x = state["prefetched"]
                x.record_stream(cur)
                with torch.cuda.stream(copy_stream):  # next step's batch: a side-stream copy that overlaps compute
                    state["prefetched"] = host.to(dev, non_blocking=True)
            else:
                x = host.to(dev)
        with rec("forward"):
            with torch.autocast(device_type=dev, dtype=torch.bfloat16, enabled=gpu):
                loss = model(x).float().pow(2).mean()
        with rec("backward"):
            loss.backward()
        with rec("optimizer"):
            opt.step()
            opt.zero_grad(set_to_none=True)
    nparam = sum(p.numel() for p in model.parameters())

    def opt_only():
        """One optimizer step on fixed gradients: isolates per-op dispatch/launch overhead from the GEMMs."""
        for p in model.parameters():
            if p.grad is None:
                p.grad = torch.full_like(p, 1e-3)
        opt.step()
    return step, {"opt_only": opt_only,"d": d, "blocks": blocks, "tokens": tokens, "params": nparam,
                  "batch_bytes": host.numel() * 4, "fixed": fixed}


def _debug_stat(out):
    """The per-layer debug statistic: .item() forces a device-to-host copy and a host wait. Returns None so the
    hook does not replace the layer's output."""
    out.detach().float().abs().mean().item()


def _py(obj):
    """numpy scalars -> Python numbers, recursively, so results.json holds numbers rather than strings."""
    if isinstance(obj, dict):
        return {k: _py(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_py(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)) and getattr(obj, "ndim", 1) == 0:
        obj = obj.item()
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


class _null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# ------------------------------------------------------------------ CUDA-event tracer (GPU side of the capture)
def make_tracer(ctx):
    torch = ctx.torch
    from torch.utils._python_dispatch import TorchDispatchMode
    from torch.utils._pytree import tree_flatten
    from torch.utils.flop_counter import flop_registry

    class Tracer(TorchDispatchMode):
        def __init__(self):
            super().__init__()
            self.rows, self.ranges, self.stack = [], [], []
            self.ref, self.ref_ns = None, 0

        def start(self):
            torch.cuda.synchronize()
            self.ref = torch.cuda.Event(enable_timing=True)
            self.ref.record()
            torch.cuda.synchronize()
            self.ref_ns = time.perf_counter_ns()

        def range(self, name: str):
            tr = self

            class R:
                def __enter__(self_):
                    self_.t0 = time.perf_counter_ns()
                    tr.stack.append(name)

                def __exit__(self_, *a):
                    tr.stack.pop()
                    tr.ranges.append((name, self_.t0, time.perf_counter_ns(), len(tr.stack)))
            return R()

        def __torch_dispatch__(self, func, types, args=(), kwargs=None):
            kwargs = kwargs or {}
            name = func._overloadpacket.__name__
            if name in NO_KERNEL_OPS:
                return func(*args, **kwargs)
            e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            stream = torch.cuda.current_stream().stream_id
            t0 = time.perf_counter_ns()
            e0.record()
            out = func(*args, **kwargs)
            e1.record()
            t1 = time.perf_counter_ns()
            ins = [a for a in tree_flatten((args, kwargs))[0] if isinstance(a, torch.Tensor)]
            outs = [a for a in tree_flatten(out)[0] if isinstance(a, torch.Tensor)]
            devs_in = {a.device.type for a in ins}
            devs_out = {a.device.type for a in outs}
            kind, copy_kind, src_mem, dst_mem, nbytes = "kernel", "", "", "", 0
            if name in ("_to_copy", "copy_") and "cpu" in (devs_in | devs_out) and "cuda" in (devs_in | devs_out):
                kind = "memcpy"
                src = ins[-1] if name == "copy_" else ins[0]
                dst = ins[0] if name == "copy_" else outs[0]
                copy_kind = "HtoD" if src.device.type == "cpu" else "DtoH"
                src_mem = ("pinned" if src.is_pinned() else "pageable") if src.device.type == "cpu" else "device"
                dst_mem = ("pinned" if dst.is_pinned() else "pageable") if dst.device.type == "cpu" else "device"
                nbytes = src.numel() * src.element_size()
            elif name == "_local_scalar_dense":     # .item(): a DtoH copy into pageable memory + a host wait
                kind, copy_kind, src_mem, dst_mem = "memcpy", "DtoH", "device", "pageable"
                nbytes = ins[0].element_size()
            try:
                f = flop_registry.get(func._overloadpacket)
                flop = float(f(*args, **kwargs, out_val=out)) if f else float(sum(o.numel() for o in outs))
            except Exception:  # noqa: BLE001 - a FLOP formula that does not apply: count one per output element
                flop = float(sum(o.numel() for o in outs))
            if kind == "memcpy":
                flop = 0.0
            seen = {}   # each distinct CUDA tensor once: compulsory traffic, a lower bound (in-place ops count once)
            for t in ins + outs:
                if t.device.type == "cuda":
                    seen[(t.data_ptr(), t.numel())] = t.numel() * t.element_size()
            mem = sum(seen.values())
            self.rows.append({"name": name, "kind": kind, "stream": stream, "e0": e0, "e1": e1, "api0": t0, "api1": t1,
                              "copy_kind": copy_kind, "src_mem": src_mem, "dst_mem": dst_mem, "bytes": nbytes,
                              "flop": flop, "dram_bytes": float(mem), "range": "/".join(self.stack)})
            return out

        def finish(self):
            torch.cuda.synchronize()
            gpu, api = [], []
            for i, r in enumerate(self.rows, 1):
                s = self.ref_ns + int(self.ref.elapsed_time(r["e0"]) * 1e6)
                e = max(s, self.ref_ns + int(self.ref.elapsed_time(r["e1"]) * 1e6))
                api_name = ("cudaMemcpyAsync" if r["kind"] == "memcpy" else "cudaLaunchKernel")
                gpu.append({"id": i, "kind": r["kind"], "name": f"aten::{r['name']}", "stream": r["stream"], "start_ns": s,
                            "end_ns": e, "correlation_id": i, "copy_kind": r["copy_kind"], "src_mem": r["src_mem"],
                            "dst_mem": r["dst_mem"], "bytes": r["bytes"], "grid_x": 0, "block_x": 0, "regs_per_thread": 0,
                            "smem_per_block_bytes": 0, "flop": r["flop"], "dram_bytes": r["dram_bytes"]})
                api.append({"correlation_id": i, "name": api_name, "start_ns": r["api0"], "end_ns": r["api1"], "thread_id": 1})
            nvtx = [{"name": n, "start_ns": a, "end_ns": b, "level": lvl} for n, a, b, lvl in self.ranges]
            return gpu, api, nvtx
    return Tracer()


def device_json(ctx, env: dict) -> dict:
    torch = ctx.torch
    p = torch.cuda.get_device_properties(0)
    g = (env.get("gpus") or [{}])[0]
    cap = (p.major, p.minor)
    name = p.name.lower()
    bits = next((b for k, b in sorted(BUS_BITS.items(), key=lambda kv: -len(kv[0])) if k in name), None)
    lim = CC_LIMITS.get(cap, CC_LIMITS[(8, 9)])
    return {"name": p.name, "compute_capability": f"{p.major}.{p.minor}", "sm_count": p.multi_processor_count,
            "evidence": "MODELED from VENDOR-SPEC: CUDA C++ Programming Guide per-CC limits; peaks = SMs x FLOP/clk/SM x "
                        "clocks.max.sm and bus width x 2 x clocks.max.memory",
            "peak_bf16_dense_flops": p.multi_processor_count * BF16_FLOP_PER_CLK_SM.get(cap, 512) * float(g["clocks.max.sm"]) * 1e6,
            "hbm_bytes_per_s": float(g["clocks.max.memory"]) * 1e6 * 2 * bits / 8 if bits else float("nan"),
            "pcie_bytes_per_s_per_dir": PCIE_GBPS_PER_LANE[int(g["pcie.link.gen.max"])] * int(g["pcie.link.width.max"]) * 1e9,
            "l2_cache_bytes": getattr(p, "L2_cache_size", 0), "regs_per_sm": p.regs_per_multiprocessor,
            "max_regs_per_thread": 255, "reg_alloc_unit_per_warp": 256, "warp_alloc_granularity": 4,
            "smem_reserved_per_block_bytes": 1024, "warp_size": p.warp_size, **lim}


def kernel_summary_no_occupancy(an):
    """The lab's kernel_summary(), minus occupancy: the tracer cannot see launch configurations."""
    pd = an.pd

    def ks(gpu, device):
        k = gpu[gpu["kind"] == "kernel"].copy()
        k["dur_ns"] = (k["end_ns"] - k["start_ns"]).clip(lower=1)
        total = k["dur_ns"].sum()
        rows = []
        for name, g in k.groupby("name", sort=False):
            secs = g["dur_ns"].sum() / 1e9
            ff = g["flop"].sum() / secs / device["peak_bf16_dense_flops"]
            bf = g["dram_bytes"].sum() / secs / device["hbm_bytes_per_s"]
            rows.append({"name": name, "count": len(g), "total_ns": int(g["dur_ns"].sum()), "mean_ns": float(g["dur_ns"].mean()),
                         "time_share": g["dur_ns"].sum() / total, "occupancy": float("nan"), "limiter": "not captured",
                         "roof_frac": max(ff, bf), "bound": "compute" if ff >= bf else "memory"})
        return pd.DataFrame(rows).sort_values("total_ns", ascending=False).reset_index(drop=True)
    return ks


def profiler_counts(ctx, step) -> dict:
    """torch.profiler over one step: CUDA runtime calls per step, and whether CUPTI delivered GPU activity."""
    torch = ctx.torch
    from torch.profiler import ProfilerActivity, profile
    acts = [ProfilerActivity.CPU] + ([ProfilerActivity.CUDA] if ctx.is_gpu else [])
    ctx.sync()
    with profile(activities=acts, record_shapes=False) as prof:
        step()
        ctx.sync()
    evs = prof.events()
    names = [e.name for e in evs]
    gpu_events = sum(1 for e in evs if str(e.device_type).endswith("CUDA"))
    launches = sum(1 for n in names if n in ("cudaLaunchKernel", "cudaLaunchKernelExC", "cuLaunchKernel"))
    syncs = sum(1 for n in names if n in ("cudaStreamSynchronize", "cudaDeviceSynchronize", "cudaEventSynchronize"))
    memcpys = sum(1 for n in names if n == "cudaMemcpyAsync")
    aten_ops = sum(1 for n in names if n.startswith("aten::") and n[6:] not in NO_KERNEL_OPS)
    by_cat: dict[str, float] = {}
    for ka in prof.key_averages():
        if ka.key.startswith("aten::"):
            c = category(ka.key[6:], "kernel")
            if ka.key[6:] in NO_KERNEL_OPS:
                continue
            by_cat[c] = by_cat.get(c, 0.0) + ka.self_cpu_time_total
    return {"gpu_activity_events": gpu_events, "cudaLaunchKernel": launches, "sync_calls": syncs,
            "cudaMemcpyAsync": memcpys, "aten_ops": aten_ops, "aten_self_cpu_us_by_category": by_cat}


def capture_gpu(ctx, an, step, dev_json: dict, n_steps: int) -> dict:
    tracer = make_tracer(ctx)
    tracer.start()
    with tracer:
        for i in range(n_steps):
            with tracer.range(f"train_step_{i + 1}"):
                step(tracer.range)
                # Close the step range only after the GPU drains. Without this, a step with no host sync (the
                # "fixed" variant) ends its CPU-side range while most of its kernels are still queued, and every
                # busy/overlap/gap figure is computed on a truncated window (Section 4.10, "NVTX ranges are
                # CPU-side"). The baseline hid the bug because its per-layer .item() syncs drained the queue.
                ctx.torch.cuda.synchronize()
    gpu, api, nvtx = tracer.finish()
    pd = an.pd
    with tempfile.TemporaryDirectory() as td:
        pd.DataFrame(gpu).to_csv(Path(td) / "gpu_trace.csv", index=False)
        pd.DataFrame(api).to_csv(Path(td) / "cuda_api_trace.csv", index=False)
        pd.DataFrame(nvtx).to_csv(Path(td) / "nvtx_ranges.csv", index=False)
        (Path(td) / "device.json").write_text(json.dumps(dev_json), encoding="utf-8")
        orig = an.kernel_summary
        an.kernel_summary = kernel_summary_no_occupancy(an)
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)   # 0/0 when a capture has no pinned copy
                res = an.analyze(td)
        finally:
            an.kernel_summary = orig
    for f in res["findings"]:
        f["evidence"] = (f["evidence"].replace("grids of 0 blocks", "grid size not captured")
                         .replace("vs nan GB/s for pinned", "(no pinned copy in this capture)"))
    # kernel classification by category, over the whole capture
    g = pd.DataFrame(gpu)
    g["dur_ns"] = g["end_ns"] - g["start_ns"]
    g["category"] = [category(n[6:], k) for n, k in zip(g["name"], g["kind"])]
    tot = g["dur_ns"].sum()
    cats = []
    for c, gg in g.groupby("category"):
        secs = max(gg["dur_ns"].sum(), 1) / 1e9
        cats.append({"category": c, "count_per_step": len(gg) / n_steps, "gpu_ms_per_step": gg["dur_ns"].sum() / 1e6 / n_steps,
                     "time_share": gg["dur_ns"].sum() / tot, "achieved_tflops": gg["flop"].sum() / secs / 1e12,
                     "achieved_gbs": gg["dram_bytes"].sum() / secs / 1e9})
    big = g[(g["kind"] == "kernel") & (g["dram_bytes"] > 2 * dev_json["l2_cache_bytes"])]
    bounds = {"max_gemm_tflops": float((g[g["category"] == "gemm"]["flop"] / (g["dur_ns"].clip(lower=1) / 1e9)).max() / 1e12),
              # Up to one L2's worth of a kernel's footprint can be served from cache (e.g. a tensor the previous op just
              # wrote), so only bytes beyond the L2 size are certain to cross DRAM: that floor is what the DRAM spec bounds.
              "max_big_kernel_gbs": float(((big["dram_bytes"] - dev_json["l2_cache_bytes"]) / (big["dur_ns"].clip(lower=1) / 1e9)).max() / 1e9)
                                    if len(big) else None}
    res["kernels"] = res["kernels"][:12]
    res = _py(res)
    return {"analysis": res, "categories": sorted(cats, key=lambda c: -c["time_share"]), "bounds": bounds,
            "ops_per_step": len(gpu) / n_steps}


def run(ctx) -> dict:
    torch = ctx.torch
    import hwlab  # noqa: E402  (shared runtime, already imported by run.py)
    an = load_solution()
    env = hwlab.environment(ctx.device)
    if not ctx.is_gpu:
        torch.set_num_threads(min(4, os.cpu_count() or 1))
    n_capt = 2 if ctx.quick else 3
    out = {"variants": {}, "notes": []}
    dev_json = device_json(ctx, env) if ctx.is_gpu else None
    for fixed in (False, True):
        name = "fixed" if fixed else "baseline"
        step, meta = build(ctx, fixed)
        for _ in range(3):                         # warm-up: allocator, cuBLAS handles, autotuning
            step()
        ctx.sync()
        opt_only = meta.pop("opt_only")
        v = {"meta": meta, "profiler": profiler_counts(ctx, step)}
        st = ctx.bench(step, warmup=2, reps=ctx.reps(10))
        v["step_time"] = st
        v["optimizer_step_time"] = ctx.bench(opt_only, warmup=3, reps=ctx.reps(20) * 2)
        if ctx.is_gpu:
            v["captures"] = [capture_gpu(ctx, an, step, dev_json, n_steps=2) for _ in range(n_capt)]
        out["variants"][name] = v
        ctx.log(f"{name:8} step median {st['median'] * 1e3:8.2f} ms  p95 {st['p95'] * 1e3:8.2f} ms  "
                f"launches/step {v['profiler']['cudaLaunchKernel']}  syncs/step {v['profiler']['sync_calls']}")
        del step
        if ctx.is_gpu:
            torch.cuda.empty_cache()
    b, f = out["variants"]["baseline"], out["variants"]["fixed"]
    out["metrics"] = {"baseline_opt_step_ms": round(b["optimizer_step_time"]["median"] * 1e3, 4),
                      "fixed_opt_step_ms": round(f["optimizer_step_time"]["median"] * 1e3, 4),
                      "baseline_step_ms": round(b["step_time"]["median"] * 1e3, 3),
                      "fixed_step_ms": round(f["step_time"]["median"] * 1e3, 3),
                      "speedup": round(b["step_time"]["median"] / f["step_time"]["median"], 3),
                      "baseline_launches_per_step": b["profiler"]["cudaLaunchKernel"],
                      "fixed_launches_per_step": f["profiler"]["cudaLaunchKernel"]}
    if ctx.is_gpu:
        out["device"] = dev_json
        prof_gpu = b["profiler"]["gpu_activity_events"]
        out["not_runnable_parts"] = []
        if prof_gpu == 0:
            out["not_runnable_parts"].append({
                "part": "GPU activity in torch.profiler / nsys (CUPTI kernel and memcpy records: launch config, registers, shared memory)",
                "probe": f"torch.profiler with ProfilerActivity.CUDA over one step: {prof_gpu} device events "
                         f"({b['profiler']['cudaLaunchKernel']} cudaLaunchKernel calls recorded on the CPU side)",
                "needs": ["CUPTI activity tracing (native Linux driver; not delivered under WSL2 here)", "Nsight Compute for counters"],
                "fallback": "CUDA-event tracer per aten op; occupancy / LOW_OCCUPANCY not evaluated"})
        out["metrics"].update({f"{k}_busy_any_frac": round(sum(s["busy_any_frac"] for c in v["captures"] for s in c["analysis"]["steps"])
                                                            / sum(len(c["analysis"]["steps"]) for c in v["captures"]), 3)
                               for k, v in out["variants"].items()})
        out["notes"] += [
            "Step time = median of >= 5 uninstrumented steps (CUDA events) after warm-up; the traced captures are separate.",
            f"{n_capt} captures of 2 steps per variant; analyze() runs on each and the spread is reported.",
            "Tracer overhead (~10-30 us host time per op) inflates launch-bound gaps; FLOPs/bytes per op are [MODELED].",
            "Pageable vs pinned and the per-layer .item() are deliberate pathologies of the baseline step."]
    else:
        out["shipped_trace_analysis"] = _py({k: v for k, v in an.analyze(PKG / "lab" / "data").items() if k in ("findings", "gaps_by_cause")})
        out["shipped_trace_analysis"]["codes"] = sorted({x["code"] for x in out["shipped_trace_analysis"]["findings"]})
        out["notes"] += ["CPU fallback: torch limited to 4 threads; step time = median of >= 5 steps (perf_counter).",
                         "The shipped trace is the lab's SIMULATED ORION capture; it is analysed here only to exercise the "
                         "pipeline in the GPU image."]
    out["tables"] = {"step_time": [{"variant": k, **{s: v["step_time"][s] for s in ("n", "median", "p95", "min", "max", "iqr")}}
                                   for k, v in out["variants"].items()]}
    return out


def _codes(cap: dict) -> set:
    return {f["code"] for f in cap["analysis"]["findings"]}


def check(result: dict, env: dict) -> list[str]:
    fails = []
    gpu = env["device"] == "cuda"
    b, f = result["variants"]["baseline"], result["variants"]["fixed"]
    ob, of = b["optimizer_step_time"]["median"], f["optimizer_step_time"]["median"]
    if gpu and of > ob:
        fails.append(f"the {'fused' if gpu else 'foreach'} AdamW step ({of * 1e3:.2f} ms) is slower than the per-parameter loop "
                     f"({ob * 1e3:.2f} ms): check the optimizer flags")
    if gpu and f["step_time"]["median"] > b["step_time"]["median"]:
        fails.append(f"fixed step {f['step_time']['median'] * 1e3:.2f} ms is not faster than baseline "
                     f"{b['step_time']['median'] * 1e3:.2f} ms: check that the fixes are active (pinned batch, no .item(), fused AdamW)")
    if f["profiler"]["cudaLaunchKernel"] > b["profiler"]["cudaLaunchKernel"] and gpu:
        fails.append("the fused optimizer did not reduce kernel launches per step: check AdamW(fused=True)")
    if not gpu:
        if f["profiler"]["aten_ops"] >= b["profiler"]["aten_ops"]:
            fails.append("the foreach optimizer and the removed hooks did not reduce aten dispatches per step: check the variants")
        shares = sum(b["profiler"]["aten_self_cpu_us_by_category"].values())
        if shares <= 0 or "gemm" not in b["profiler"]["aten_self_cpu_us_by_category"]:
            fails.append("CPU profiler capture has no GEMM time: check that torch.profiler recorded aten ops")
        need = {"PAGEABLE_H2D", "EXCESS_SYNC", "LAUNCH_BOUND", "STREAM_DEPENDENCY", "LOW_OCCUPANCY"}
        if not need <= set(result["shipped_trace_analysis"]["codes"]):
            fails.append(f"analyze() on the shipped trace found {result['shipped_trace_analysis']['codes']}, expected {sorted(need)}")
        return fails
    dev = result["device"]
    # Window sanity: a traced step can be slower than the uninstrumented median (tracer overhead) but never much
    # shorter. A window below ~90 % of the median step means the range closed before the GPU finished.
    for name, v in result["variants"].items():
        med_ns = v["step_time"]["median"] * 1e9
        for c in v["captures"]:
            for s in c["analysis"]["steps"]:
                if s["window_ns"] < 0.9 * med_ns:
                    fails.append(f"{name} {s['step']}: traced window {s['window_ns'] / 1e6:.1f} ms < 90 % of the measured median "
                                 f"step {med_ns / 1e6:.1f} ms: the trace range closed before the GPU drained (Section 4.10)")
    if b["profiler"]["sync_calls"] <= f["profiler"]["sync_calls"]:
        fails.append("baseline should make more host syncs per step than the fixed step (the per-layer .item())")
    for name, v in result["variants"].items():
        for c in v["captures"]:
            for s in c["analysis"]["steps"]:
                if not (0 <= s["busy_kernel_frac"] <= s["busy_any_frac"] <= 1.0):
                    fails.append(f"{name} {s['step']}: busy fractions out of order ({s['busy_kernel_frac']:.3f}, {s['busy_any_frac']:.3f})")
            for cp in c["analysis"]["copies"]:
                if cp["copy_kind"] == "HtoD" and cp["bytes"] >= 1 << 20 and cp["gbps"] > 1.05 * dev["pcie_bytes_per_s_per_dir"] / 1e9:
                    fails.append(f"{name}: H2D copy at {cp['gbps']:.1f} GB/s exceeds the PCIe link: check the tracer's clock conversion")
            if c["bounds"]["max_gemm_tflops"] > 1.02 * dev["peak_bf16_dense_flops"] / 1e12:
                fails.append(f"{name}: a GEMM ran at {c['bounds']['max_gemm_tflops']:.1f} TFLOP/s, above the BF16 peak: check the FLOP count")
            mb = c["bounds"]["max_big_kernel_gbs"]
            if mb and mb > 1.02 * dev["hbm_bytes_per_s"] / 1e9:
                fails.append(f"{name}: a > 2xL2 kernel moved {mb:.0f} GB/s of guaranteed DRAM traffic (footprint minus L2), above the DRAM spec: check the byte count")
    for c in b["captures"]:
        if "PAGEABLE_H2D" not in _codes(c):
            fails.append("baseline capture lacks PAGEABLE_H2D: the pageable batch copy it contains on purpose was not detected")
    # EXCESS_SYNC needs a sync call's end to land inside a GPU-idle gap of ~0.1 ms. With GPU intervals rebuilt
    # from CUDA events on the host clock (plus 10-30 us of tracer time per op), that alignment varies from one
    # capture to the next, so require it in at least one capture. The sync-count invariant above is the robust check.
    if b["captures"] and not any("EXCESS_SYNC" in _codes(c) for c in b["captures"]):
        fails.append("no baseline capture reports EXCESS_SYNC: the per-layer .item() syncs were not detected in any capture")
    for c in f["captures"]:
        extra = {"PAGEABLE_H2D", "EXCESS_SYNC"} & _codes(c)
        if extra:
            fails.append(f"fixed capture still reports {sorted(extra)}: check pin_memory/non_blocking and that the hooks are gone")
    hb = [cp["gbps"] for c in b["captures"] for cp in c["analysis"]["copies"] if cp["copy_kind"] == "HtoD" and cp["bytes"] >= 1 << 20]
    hf = [cp["gbps"] for c in f["captures"] for cp in c["analysis"]["copies"] if cp["copy_kind"] == "HtoD" and cp["bytes"] >= 1 << 20]
    if hb and hf and sorted(hf)[len(hf) // 2] < 0.95 * sorted(hb)[len(hb) // 2]:
        fails.append("pinned H2D (fixed) slower than pageable (baseline): check that the host batch is pinned")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    V = result["variants"]
    m = result["metrics"]
    L = ["## Workload", "",
         f"MLP of {V['baseline']['meta']['blocks']} blocks (d = {V['baseline']['meta']['d']}, 4d hidden), "
         f"{V['baseline']['meta']['params'] / 1e6:.1f} M parameters, {V['baseline']['meta']['tokens']} tokens per step, "
         f"{'BF16 autocast' if gpu else 'FP32'}, AdamW. **Baseline**: pageable batch copy, a `.item()` debug hook on every "
         "Linear, per-parameter (for-loop) AdamW. **Fixed**: pinned batch prefetched one step ahead with `non_blocking=True`, "
         "no hook, fused AdamW" + ("" if gpu else " (foreach on the CPU)") + ".", "",
         "## Step time, uninstrumented (Chapter 6 protocol)", "",
         "| Variant | n | Median (ms) | p95 (ms) | IQR (ms) | min-max (ms) | Optimizer step alone, median (p95) ms | Kernel launches / step | Host syncs / step |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k, v in V.items():
        s, p, o = v["step_time"], v["profiler"], v["optimizer_step_time"]
        L.append(f"| {k} | {s['n']} | {s['median'] * 1e3:.2f} | {s['p95'] * 1e3:.2f} | {s['iqr'] * 1e3:.2f} | "
                 f"{s['min'] * 1e3:.2f}-{s['max'] * 1e3:.2f} | {o['median'] * 1e3:.3f} ({o['p95'] * 1e3:.3f}) | "
                 f"{p['cudaLaunchKernel']} | {p['sync_calls']} |")
    L += ["", f"Speed-up from the fixes: **{m['speedup']:.2f}x** `[MEASURED]`. Launch and sync counts are from torch.profiler's "
          "CUDA runtime records (CPU side) over one step; the sync count includes the capture's own closing synchronize." if gpu else
          f"Whole-step ratio on the CPU: {m['speedup']:.2f}x. The GEMMs dominate a CPU step and the device-side fixes have "
          "nothing to fix (no H2D copy, `.item()` waits for no device), so this ratio is noise around 1; the optimizer step "
          "alone shows why: the foreach AdamW cuts aten dispatches per step "
          f"({V['baseline']['profiler']['aten_ops']} -> {V['fixed']['profiler']['aten_ops']}), but on a CPU the update of "
          "million-element weights is memory-bound, not dispatch-bound, so it need not be faster. On a GPU each dispatch is "
          "a kernel launch, and the same change removes launch-bound gaps."]
    if gpu:
        for k, v in V.items():
            caps = v["captures"]
            steps = [s for c in caps for s in c["analysis"]["steps"]]
            L += ["", f"## Trace analysis: {k} ({len(caps)} captures x 2 steps, lab `analyze()`)", "",
                  "| Metric | Median | min-max over steps |", "|---|---|---|"]
            for key, lab, scale in (("step_ms", "traced step (ms)", 1), ("busy_any_frac", "GPU busy, any activity", 100),
                                    ("busy_kernel_frac", "GPU busy, kernels", 100), ("overlap_frac", "copy overlapped with compute", 100)):
                xs = sorted(s[key] * scale for s in steps)
                unit = " %" if scale == 100 else ""
                L.append(f"| {lab} | {xs[len(xs) // 2]:.1f}{unit} | {xs[0]:.1f}-{xs[-1]:.1f}{unit} |")
            gaps = {}
            for s in steps:
                for cause, g in s["gaps"].items():
                    gaps.setdefault(cause, []).append(g["ms"])
            L.append(f"| idle gaps by cause (ms/step, median) | "
                     f"{', '.join(f'{c} {sorted(x)[len(x) // 2]:.2f}' for c, x in sorted(gaps.items())) or 'none'} | |")
            c0 = caps[0]
            L += ["", "Kernel classification (GPU time per step, capture 1):", "",
                  "| Category | Ops / step | GPU ms / step | Share | Achieved TFLOP/s | Achieved GB/s |", "|---|---|---|---|---|---|"]
            for c in c0["categories"]:
                L.append(f"| {c['category']} | {c['count_per_step']:.0f} | {c['gpu_ms_per_step']:.2f} | {c['time_share'] * 100:.1f} % | "
                         f"{c['achieved_tflops']:.2f} | {c['achieved_gbs']:.1f} |")
            L += ["", "Findings (capture 1, ranked by estimated saving):", ""]
            for i, fd in enumerate(sorted(c0["analysis"]["findings"], key=lambda x: -x["est_saving_ms_per_step"]), 1):
                L.append(f"{i}. **{fd['code']}** ≈ {fd['est_saving_ms_per_step']:.2f} ms/step — {fd['evidence']}")
            if not c0["analysis"]["findings"]:
                L.append("none")
            L += ["", "Top kernels by GPU time (roof fraction vs this GPU's BF16 peak / DRAM bandwidth; occupancy not captured):", "",
                  "| Op | Count | Total (ms) | Share | Bound | % of roof |", "|---|---|---|---|---|---|"]
            for r in c0["analysis"]["kernels"][:6]:
                L.append(f"| {r['name']} | {r['count']} | {r['total_ns'] / 1e6:.2f} | {r['time_share'] * 100:.1f} % | {r['bound']} | "
                         f"{r['roof_frac'] * 100:.0f} % |")
        d = result["device"]
        L += ["", f"Device file: {d['name']}, CC {d['compute_capability']}, {d['sm_count']} SMs, BF16 peak "
              f"{d['peak_bf16_dense_flops'] / 1e12:.1f} TFLOP/s, DRAM {d['hbm_bytes_per_s'] / 1e9:.0f} GB/s, PCIe "
              f"{d['pcie_bytes_per_s_per_dir'] / 1e9:.2f} GB/s per direction `[MODELED from VENDOR-SPEC]`. The manuscript's worked "
              "example is an H100-class GPU (132 SMs, 989 TFLOP/s, 3.35 TB/s, Gen5 x16): **this is a laptop Ada GPU, not an H100**, "
              "so the absolute times differ; the pathologies and their signatures in the timeline are the same.",
              "", "## What to conclude", "",
              "- The baseline's gaps are named by their causes: the pageable copy blocks the host and cannot overlap, every "
              "`.item()` drains the queue (host_sync gaps), and the per-parameter optimizer issues bursts of tiny kernels that "
              "the GPU retires faster than the CPU can launch them (launch_bound gaps).",
              "- The fixes remove the first two findings outright and shrink the third; the uninstrumented step-time ratio is the "
              "number to report, not the traced one (the tracer itself costs host time per op).",
              "- `GPU busy` is not efficiency (Section 4.9): read it next to the roof fractions of the top kernels.",
              "- A roof fraction above 100 % (for example GELU on a 16 MiB activation) is not a measurement error in the time: "
              "the working set fits in this GPU's 32 MiB L2, so the bytes never reached DRAM (exercise 6.3's mechanism). Only "
              "kernels larger than 2x L2 are held to the DRAM bound in check(), and only for the bytes beyond one L2's worth, since "
              "that much of the footprint can still hit in cache.",
              "- Small STREAM_DEPENDENCY gaps (tens of µs) show up in both variants; part of each is the tracer's own "
              "event-record commands on the stream, so they are reported but not acted on."]
    else:
        L += ["", "## CPU capture: aten self time by category (baseline vs fixed, torch.profiler)", "",
              "| Category | Baseline (us) | Fixed (us) |", "|---|---|---|"]
        cb, cf = V["baseline"]["profiler"]["aten_self_cpu_us_by_category"], V["fixed"]["profiler"]["aten_self_cpu_us_by_category"]
        for c in sorted(set(cb) | set(cf), key=lambda c: -cb.get(c, 0)):
            L.append(f"| {c} | {cb.get(c, 0):.0f} | {cf.get(c, 0):.0f} |")
        sh = result["shipped_trace_analysis"]
        L += ["", f"Lab `analyze()` on the shipped SIMULATED ORION trace: findings {', '.join(sh['codes'])}; gaps by cause "
              f"{sh['gaps_by_cause']}.", "",
              "_CPU fallback: no GPU was used. There is no GPU timeline, no PCIe copy and no device to sync with, so the "
              "trace-schema export, the gap attribution on real data and the GPU-only invariants (PCIe and roof bounds, "
              "sync and pageable findings) were skipped._"]
    if result.get("not_runnable_parts"):
        L += ["", "## Not runnable on this host (probed, not faked)", "", "| Part | Probe | Needs | Used instead |", "|---|---|---|---|"]
        for p in result["not_runnable_parts"]:
            L.append(f"| {p['part']} | {p['probe']} | {', '.join(p['needs'])} | {p['fallback']} |")
    return "\n".join(L)
