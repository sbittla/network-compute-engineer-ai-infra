"""Capstone H L2: calibrate the serving roofline (mfu_prefill, hbm_eff, step_overhead_s) on one real GPU.

What it teaches (starter-kit README section 8, L2; manuscript Ch 19-20 roofline): prefill is
compute-bound and decode is memory-bound, and the three efficiency constants the L1 capacity model
assumes can be *measured* instead of guessed. The experiment builds a small randomly initialised
decoder-only transformer (no download, no network), measures prefill latency against prompt length
(output length 1) and decode step time against batch size at a fixed context, fits the three
constants with the L1 formulas (``prefill_time_s`` and ``decode_step_time_s`` from the reference
model, re-pointed at the small model's dimensions), checks that the fitted model predicts the
measured points, and reruns the L1 pool sizing with the fitted constants as a what-if.

Not runnable on one host: the L3 KV-cache path between two RDMA nodes (ib_write_bw --use_cuda,
GPUDirect RDMA, iperf3 baseline). The probe records it; the only KV transfer path that exists here,
GPU -> pinned host memory over PCIe, is measured as a single-host stand-in.

CPU fallback: the same model (smaller, fp32) on the CPU. The "peak" FLOP/s and bytes/s are a
measured dense GEMM and a measured memory copy on this CPU, so the fitted constants are relative to
measured ceilings rather than a vendor peak. GPU-only invariants are skipped.
"""
from __future__ import annotations

import importlib.util
import math
import os
import shutil
import statistics
import sys
import time
from pathlib import Path

EXPERIMENT = {
    "id": "capstone-h-l2",
    "title": "Capstone H L2: roofline calibration of prefill and decode on one GPU",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same random-weight transformer, smaller and fp32, on the CPU; peak FLOP/s and "
                     "bytes/s are a measured GEMM and memory copy, so the fitted mfu/hbm_eff are relative to "
                     "measured CPU ceilings; the RDMA KV path is recorded as not runnable"),
}

PKG = Path(__file__).resolve().parents[2]
# Memory bus width (bits) for GPUs whose peak bandwidth nvidia-smi cannot report [VENDOR-SPEC, 2026-10].
BUS_BITS = {"rtx 4060 laptop": 128, "rtx 4060": 128, "rtx 4070 laptop": 128, "rtx 4090": 384, "rtx 3090": 384}


def load_l1(name: str):
    """The L1 model: the instructor reference if present, else the learner's starter implementation."""
    for p in (PKG / "instructor" / "reference" / f"{name}.py", PKG / "starter-kit" / "starter" / f"{name}.py"):
        if p.is_file():
            sys.path.insert(0, str(PKG / "starter-kit"))
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


def gpu_peaks(env: dict) -> dict:
    """Upper-bound peaks for this GPU from SM count and max SM clock (Ada whitepaper per-SM rates)."""
    g = (env.get("gpus") or [{}])[0]
    sm = env.get("gpu0", {}).get("sm_count")
    clk = num(g.get("clocks.max.sm"))
    out = {"source": "SMs x per-SM rate x clocks.max.sm (NVIDIA Ada architecture whitepaper) [VENDOR-SPEC]"}
    if sm and clk:
        out["fp32_flops"] = sm * 256 * clk * 1e6           # 128 FP32 lanes x 2 FLOP/FMA
        out["fp16_tc_flops"] = sm * 512 * clk * 1e6        # dense FP16 tensor, FP32 accumulate (GeForce Ada)
    name = (g.get("name") or "").lower()
    mclk = num(g.get("clocks.max.memory"))
    bits = next((b for k, b in BUS_BITS.items() if k in name), None)
    if bits and mclk:
        out["mem_bw"] = 2 * mclk * 1e6 * bits / 8          # GDDR6: 2 transfers per reported clock
    return out


# ---------------------------------------------------------------------------------- the model
class Decoder:
    """Random-weight decoder-only transformer with a preallocated KV cache (inference only)."""

    def __init__(self, torch, *, d: int, layers: int, heads: int, vocab: int, dtype, device: str,
                 max_batch: int, max_len: int):
        self.t, self.d, self.L, self.H, self.hd, self.V = torch, d, layers, heads, d // heads, vocab
        g = torch.Generator().manual_seed(0)
        mk = lambda *s: (torch.randn(*s, generator=g) * 0.02).to(device=device, dtype=dtype)  # noqa: E731
        self.emb = mk(vocab, d)
        self.w = [{"qkv": mk(d, 3 * d), "o": mk(d, d), "up": mk(d, 4 * d), "down": mk(4 * d, d)} for _ in range(layers)]
        self.k = torch.zeros(layers, max_batch, heads, max_len, self.hd, device=device, dtype=dtype)
        self.v = torch.zeros_like(self.k)
        self.dtype, self.device = dtype, device

    @property
    def params_nonembed(self) -> int:
        return 12 * self.L * self.d * self.d

    @property
    def weight_bytes(self) -> int:
        return (self.params_nonembed + self.V * self.d) * self.emb.element_size()

    @property
    def kv_bytes_per_token(self) -> int:
        return 2 * self.L * self.d * self.emb.element_size()

    def _block(self, x, l, attend):
        F = self.t.nn.functional
        w = self.w[l]
        h = F.layer_norm(x, (self.d,))
        q, k, v = (h @ w["qkv"]).split(self.d, dim=-1)
        B, T, _ = q.shape
        q, k, v = (z.view(B, T, self.H, self.hd).transpose(1, 2) for z in (q, k, v))
        a = attend(l, q, k, v)
        x = x + a.transpose(1, 2).reshape(B, T, self.d) @ w["o"]
        h = F.layer_norm(x, (self.d,))
        return x + F.gelu(h @ w["up"]) @ w["down"]

    def prefill(self, tokens, slot: int):
        """Prompt ``tokens`` [T] into cache slot ``slot``; returns the first generated token."""
        T = tokens.shape[0]
        F = self.t.nn.functional

        def attend(l, q, k, v):
            self.k[l, slot, :, :T] = k[0]
            self.v[l, slot, :, :T] = v[0]
            return F.scaled_dot_product_attention(q, k, v, is_causal=True)

        x = self.emb[tokens][None]
        for l in range(self.L):
            x = self._block(x, l, attend)
        return (F.layer_norm(x[:, -1], (self.d,)) @ self.emb.T).argmax(-1)

    def decode(self, tokens, lens):
        """One decode step for slots 0..n-1 (``lens`` = tokens already cached per slot)."""
        t = self.t
        F = t.nn.functional
        n = tokens.shape[0]
        lmax = int(lens.max()) + 1
        rows = t.arange(n, device=self.device)
        mask = (t.arange(lmax, device=self.device)[None, :] <= lens[:, None])[:, None, None, :]

        def attend(l, q, k, v):
            self.k[l, rows, :, lens] = k[:, :, 0]
            self.v[l, rows, :, lens] = v[:, :, 0]
            return F.scaled_dot_product_attention(q, self.k[l, :n, :, :lmax], self.v[l, :n, :, :lmax], attn_mask=mask)

        x = self.emb[tokens][:, None]
        for l in range(self.L):
            x = self._block(x, l, attend)
        return (F.layer_norm(x[:, -1], (self.d,)) @ self.emb.T).argmax(-1)


# ---------------------------------------------------------------------------------- measurement
def measured_ceilings(ctx) -> dict:
    """Dense GEMM FLOP/s and device-memory copy bytes/s actually achievable here (same dtype as the model)."""
    torch = ctx.torch
    dt = torch.float16 if ctx.is_gpu else torch.float32
    n = 4096 if ctx.is_gpu else 1024
    a, b = torch.randn(n, n, device=ctx.device, dtype=dt), torch.randn(n, n, device=ctx.device, dtype=dt)
    g = ctx.bench(lambda: a @ b, warmup=3, reps=ctx.reps(10))
    m = (256 if ctx.is_gpu else 128) * 2 ** 20
    src, dst = torch.empty(m, dtype=torch.uint8, device=ctx.device), torch.empty(m, dtype=torch.uint8, device=ctx.device)
    c = ctx.bench(lambda: dst.copy_(src), warmup=3, reps=ctx.reps(10))
    return {"gemm_flops": 2 * n ** 3 / g["median"], "gemm_n": n, "copy_bytes_per_s": 2 * m / c["median"],
            "copy_mib": m // 2 ** 20}


def allocatable_bytes(torch, chunk: int = 256 * 2 ** 20) -> int:
    """Device memory this process can actually allocate now: claim chunks until OOM, then release them."""
    held = []
    try:
        while True:
            held.append(torch.empty(chunk, dtype=torch.uint8, device="cuda"))
    except torch.OutOfMemoryError:
        pass
    n = len(held) * chunk
    del held
    torch.cuda.empty_cache()
    return n


def interleaved(ctx, cases: dict, reps: int, warmup: int = 3) -> dict:
    """Round-robin timing: each repetition times every case once, so slow drifts (clock changes, another
    tenant on the GPU) hit all cases alike instead of biasing whichever case ran during the disturbance."""
    import hwlab
    torch = ctx.torch
    for _ in range(warmup):
        for f in cases.values():
            f()
    ctx.sync()
    samples = {k: [] for k in cases}
    for _ in range(reps):
        for k, f in cases.items():
            if ctx.is_gpu:
                e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                e0.record()
                f()
                e1.record()
                torch.cuda.synchronize()
                samples[k].append(e0.elapsed_time(e1) / 1000.0)
            else:
                t0 = time.perf_counter()
                f()
                samples[k].append(time.perf_counter() - t0)
    return {k: hwlab.summarize(v) for k, v in samples.items()}


def kv_path_probe() -> dict:
    ib = Path("/sys/class/infiniband")
    devs = sorted(os.listdir(ib)) if ib.is_dir() else []
    return {"rdma_devices": devs, "dev_infiniband": Path("/dev/infiniband").exists(),
            "ib_write_bw": bool(shutil.which("ib_write_bw")), "iperf3": bool(shutil.which("iperf3")),
            "nvidia_peermem": "nvidia_peermem" in (Path("/proc/modules").read_text() if Path("/proc/modules").exists() else "")}


def run(ctx) -> dict:
    torch = ctx.torch
    gpu = ctx.is_gpu
    if not gpu:   # a bounded thread count: oversubscribed BLAS threads on a shared host make CPU timings erratic
        torch.set_num_threads(min(8, os.cpu_count() or 1))
        ctx.log(f"CPU threads: {torch.get_num_threads()}")
    if gpu:
        cfg = dict(d=2048, layers=8, heads=16, vocab=8192, dtype=torch.float16)
        prompts = [64, 256, 1024] if ctx.quick else [64, 128, 256, 512, 1024, 2048]
        batches = [1, 4, 16] if ctx.quick else [1, 2, 4, 8, 16, 32]
        ctx_len = 512
    else:
        cfg = dict(d=512, layers=4, heads=8, vocab=4096, dtype=torch.float32)
        prompts = [32, 128, 512] if ctx.quick else [32, 64, 128, 256, 512, 1024]
        batches = [1, 4, 16] if ctx.quick else [1, 2, 4, 8, 16, 32]
        ctx_len = 256
    max_len = max(max(prompts), ctx_len) + 8
    # Ceilings first, then release their buffers: they must not share VRAM with the model and KV cache.
    ceil = measured_ceilings(ctx)
    mem_notes = []
    if gpu:
        torch.cuda.empty_cache()
        # A desktop GPU shares VRAM with the display and other apps. Under WSL2, cudaMemGetInfo reports memory that
        # Windows is holding as free, so measure what can really be allocated, then drop the largest batches until
        # weights + KV + a 1 GiB reserve fit in 90 % of it.
        free = allocatable_bytes(torch)
        esz = torch.empty((), dtype=cfg["dtype"]).element_size()
        weights = (12 * cfg["layers"] * cfg["d"] ** 2 + cfg["vocab"] * cfg["d"]) * esz
        kv = lambda b: 2 * cfg["layers"] * b * max_len * cfg["d"] * esz   # noqa: E731
        dropped = []
        while len(batches) > 3 and weights + kv(max(batches)) + 2 ** 30 > 0.9 * free:
            dropped.append(batches.pop())
        if dropped:
            mem_notes.append(f"Allocatable VRAM at start was {free / 2 ** 30:.2f} GiB (probed; cudaMemGetInfo overstates it under WSL2), so batches {sorted(dropped)} were dropped to fit "
                             f"the KV cache (weights {weights / 2 ** 30:.2f} GiB + KV {kv(max(batches)) / 2 ** 30:.2f} GiB).")
            ctx.log(mem_notes[-1])
    m = Decoder(torch, device=ctx.device, max_batch=max(batches), max_len=max_len, **cfg)
    ctx.log(f"model d={m.d} L={m.L} non-embedding params={m.params_nonembed / 1e6:.0f} M, weights {m.weight_bytes / 1e6:.0f} MB; "
            f"measured GEMM {ceil['gemm_flops'] / 1e12:.2f} TFLOP/s, copy {ceil['copy_bytes_per_s'] / 1e9:.1f} GB/s")
    gen = torch.Generator().manual_seed(1)

    prefill_rows = []
    with torch.inference_mode():
        ptoks = {T: torch.randint(0, m.V, (T,), generator=gen).to(ctx.device) for T in prompts}
        stats = interleaved(ctx, {T: (lambda t=t: m.prefill(t, 0)) for T, t in ptoks.items()}, ctx.reps(10))
        for T in prompts:
            st = stats[T]
            flops = 2 * m.params_nonembed * T + 2 * m.L * m.d * T ** 2      # the L1 prefill FLOP formula
            prefill_rows.append({"prompt_tokens": T, "median_s": st["median"], "p95_s": st["p95"], "iqr_s": st["iqr"],
                                 "n": st["n"], "flops": flops, "tflops_s": flops / st["median"] / 1e12,
                                 "tokens_per_s": T / st["median"]})
            ctx.log(f"prefill T={T:5d}: {st['median'] * 1e3:8.2f} ms  {flops / st['median'] / 1e12:6.2f} TFLOP/s")

        m.k[:, :, :, :ctx_len].normal_(0, 0.02)                  # every slot holds a ctx_len-token context
        m.v[:, :, :, :ctx_len].normal_(0, 0.02)
        dcases = {}
        for B in batches:
            lens = torch.full((B,), ctx_len, device=ctx.device, dtype=torch.long)
            toks = torch.randint(0, m.V, (B,), generator=gen).to(ctx.device)
            dcases[B] = lambda t=toks, n=lens: m.decode(t, n)
        stats = interleaved(ctx, dcases, ctx.reps(20))
        decode_rows = []
        for B in batches:
            st = stats[B]
            byts = m.weight_bytes + B * (ctx_len + 1) * m.kv_bytes_per_token  # the L1 decode byte formula
            decode_rows.append({"batch": B, "ctx_tokens": ctx_len, "median_s": st["median"], "p95_s": st["p95"],
                                "iqr_s": st["iqr"], "n": st["n"], "bytes": byts, "gbs": byts / st["median"] / 1e9,
                                "tok_per_s": B / st["median"]})
            ctx.log(f"decode B={B:3d} ctx={ctx_len}: {st['median'] * 1e3:7.3f} ms/step  {byts / st['median'] / 1e9:6.1f} GB/s")

        kv = measure_kv_offload(ctx, m, prompts)

    peaks = {"flops": ceil["gemm_flops"], "bw": ceil["copy_bytes_per_s"], "basis": "measured GEMM / copy on this device"}
    fit = fit_constants(prefill_rows, decode_rows, peaks)
    result = {"metrics": {}, "tables": {"prefill": prefill_rows, "decode": decode_rows, "kv_offload": kv},
              "model": {"d": m.d, "layers": m.L, "heads": m.H, "vocab": m.V, "dtype": str(cfg["dtype"]),
                        "params_nonembed": m.params_nonembed, "weight_bytes": m.weight_bytes,
                        "kv_bytes_per_token": m.kv_bytes_per_token},
              "ceilings": ceil, "fit_measured_ceiling": fit, "probe": kv_path_probe(), "notes": list(mem_notes)}
    result["metrics"].update({"mfu_prefill_vs_measured_gemm": round(fit["mfu_prefill"], 3),
                              "hbm_eff_vs_measured_copy": round(fit["hbm_eff"], 3),
                              "step_overhead_ms": round(fit["step_overhead_s"] * 1e3, 3),
                              "decode_ms_b1": round(decode_rows[0]["median_s"] * 1e3, 3)})
    probe = result["probe"]
    result["not_runnable_parts"] = [{
        "part": "L3 KV-cache transfer between two RDMA nodes (ib_write_bw --use_cuda, GPUDirect RDMA, TCP baseline)",
        "probe": f"/sys/class/infiniband devices={probe['rdma_devices'] or 'none'}, /dev/infiniband={probe['dev_infiniband']}, "
                 f"ib_write_bw={'present' if probe['ib_write_bw'] else 'absent'}, torch.cuda.device_count()="
                 f"{torch.cuda.device_count() if gpu else 0}",
        "needs": ["two GPU nodes", "RDMA NIC per rail (GPUDirect RDMA capable)", "lab switch", "perftest built with CUDA"],
        "fallback": "GPU -> pinned host memory KV offload over PCIe measured instead (table kv_offload)" if gpu
                    else "host-memory KV copy measured instead (table kv_offload)",
    }]
    result["notes"] += [
        "Model: random weights, greedy argmax; output quality is irrelevant, only the cost of the work.",
        "Prefill FLOPs = 2*N*T + 2*L*d*T^2 and decode bytes = weights + B*ctx*KV bytes/token, the L1 formulas; "
        "l1_formula_crosscheck evaluates serve.prefill_time_s / decode_step_time_s themselves with MODEL re-pointed at this model.",
        "Repetitions: 3 warm-ups, >= 5 timed, interleaved round-robin across sizes; CUDA events on the GPU, perf_counter on the CPU; medians reported.",
    ]
    if gpu:
        vp = gpu_peaks(probe_env(ctx))
        result["vendor_peaks"] = vp
        if vp.get("fp16_tc_flops") and vp.get("mem_bw"):
            fv = fit_constants(prefill_rows, decode_rows, {"flops": vp["fp16_tc_flops"], "bw": vp["mem_bw"], "basis": "vendor peak"})
            result["fit_vendor_peak"] = fv
            result["metrics"].update({"mfu_prefill_vs_vendor_peak": round(fv["mfu_prefill"], 3),
                                      "hbm_eff_vs_vendor_peak": round(fv["hbm_eff"], 3)})
    # The L1 what-if uses constants relative to a vendor peak, as the L1 hardware table does.
    result["l1_sizing_whatif"] = l1_whatif(result.get("fit_vendor_peak", fit))
    result["l1_formula_crosscheck"] = l1_crosscheck(m, result.get("fit_vendor_peak", fit), prefill_rows, decode_rows)
    return result


def l1_crosscheck(m, fit, prefill_rows, decode_rows) -> dict:
    """Evaluate the L1 reference formulas themselves (MODEL re-pointed at this model) with the fitted constants,
    and confirm they give the same predictions as the fit used here."""
    ref, src = load_l1("serve")
    if ref is None or not hasattr(ref, "MODEL"):
        return {"available": False}
    saved = dict(ref.MODEL)
    try:
        ref.MODEL.update({"params": m.params_nonembed, "layers": m.L, "d_model": m.d, "kv_heads": m.H, "head_dim": m.hd,
                          "bytes_per_elem": m.emb.element_size(), "weights_GB": m.weight_bytes / 1e9})
        hw = {"gpus_per_instance": 1, "peak_TFLOPs": fit["peak_flops"] / 1e12, "hbm_TBps": fit["peak_bw"] / 1e12,
              "mfu_prefill": fit["mfu_prefill"], "hbm_eff": fit["hbm_eff"], "step_overhead_s": fit["step_overhead_s"]}
        pre = [ref.prefill_time_s(r["prompt_tokens"], hw) for r in prefill_rows]
        dec = [ref.decode_step_time_s(r["batch"], r["batch"] * (r["ctx_tokens"] + 1), hw) for r in decode_rows]
    except NotImplementedError:
        return {"available": False, "why": "starter serve.py not implemented yet"}
    finally:
        ref.MODEL.clear()
        ref.MODEL.update(saved)
    mine = [p["modeled_s"] for p in fit["pred_prefill"]] + [p["modeled_s"] for p in fit["pred_decode"]]
    dev = max(abs(a - b) / b for a, b in zip(pre + dec, mine))
    return {"available": True, "source": src, "max_rel_diff": dev, "prefill_s": pre, "decode_s": dec}


def probe_env(ctx) -> dict:
    """The parts of the environment manifest run() needs (run.py passes the full manifest only to check/report)."""
    import hwlab  # the shared runtime (/opt/hwlab), on sys.path when run through run.py
    p = ctx.torch.cuda.get_device_properties(0)
    return {"gpus": hwlab.nvidia_smi_query(hwlab.NVSMI_FIELDS), "gpu0": {"sm_count": p.multi_processor_count, "name": p.name}}


def measure_kv_offload(ctx, m, prompts) -> list[dict]:
    """KV for one prompt copied device -> pinned host (the transfer path that exists on one host)."""
    torch = ctx.torch
    rows = []
    for T in prompts[-2:]:
        nbytes = T * m.kv_bytes_per_token
        src = torch.empty(nbytes, dtype=torch.uint8, device=ctx.device)
        dst = torch.empty(nbytes, dtype=torch.uint8, pin_memory=ctx.is_gpu)
        st = ctx.bench(lambda: dst.copy_(src, non_blocking=ctx.is_gpu), warmup=3, reps=ctx.reps(10))
        rows.append({"prompt_tokens": T, "kv_bytes": nbytes, "median_s": st["median"], "p95_s": st["p95"],
                     "gbs": nbytes / st["median"] / 1e9, "path": "GPU->pinned host (PCIe)" if ctx.is_gpu else "host memcpy"})
    return rows


def fit_constants(prefill_rows, decode_rows, peaks) -> dict:
    """Fit the L1 constants. mfu: least squares through the origin on the compute-bound prompts (T >= 256,
    or the largest two); decode: ordinary least squares t = bytes / (bw * hbm_eff) + step_overhead."""
    big = [r for r in prefill_rows if r["prompt_tokens"] >= 256] or prefill_rows[-2:]
    x = [r["flops"] / peaks["flops"] for r in big]
    y = [r["median_s"] for r in big]
    mfu = sum(a * a for a in x) / sum(a * b for a, b in zip(x, y))
    xs = [r["bytes"] for r in decode_rows]
    ys = [r["median_s"] for r in decode_rows]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((a - mx) ** 2 for a in xs)
    slope = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / sxx if sxx > 0 else 0.0
    if slope <= 0:      # flat in bytes (overhead-bound): attribute the smallest step to bandwidth + overhead
        slope = min(ys) / max(xs) / 2
    overhead = max(0.0, my - slope * mx)
    hbm_eff = 1.0 / (slope * peaks["bw"])
    pred_p = [{"prompt_tokens": r["prompt_tokens"], "measured_s": r["median_s"], "modeled_s": r["flops"] / (peaks["flops"] * mfu)}
              for r in prefill_rows]
    pred_d = [{"batch": r["batch"], "measured_s": r["median_s"], "modeled_s": r["bytes"] * slope + overhead} for r in decode_rows]
    for row in pred_p + pred_d:
        row["rel_err"] = (row["modeled_s"] - row["measured_s"]) / row["measured_s"]
    return {"basis": peaks["basis"], "peak_flops": peaks["flops"], "peak_bw": peaks["bw"], "mfu_prefill": mfu,
            "hbm_eff": hbm_eff, "step_overhead_s": overhead, "prefill_fit_points": [r["prompt_tokens"] for r in big],
            "pred_prefill": pred_p, "pred_decode": pred_d}


def l1_whatif(fit: dict) -> dict:
    """Rerun the L1 pool sizing for the H100-class instance with the efficiencies measured here [MODELED]."""
    ref, src = load_l1("serve")
    if ref is None:
        return {"available": False, "why": "no L1 model found (instructor/reference/serve.py or starter/serve.py)"}
    try:
        data = ref.load_dataset(PKG / "starter-kit" / "data")
        base = ref.hw_profile(data["hardware"], "h100-class")
        meas = ref.hw_profile(data["hardware"], "h100-class", mfu_prefill=min(fit["mfu_prefill"], 1.0),
                              hbm_eff=min(fit["hbm_eff"], 1.0))
        rho = data["config"]["rho_max"]
        a = ref.size_pools(data["trace"], base, base, data["slo"], rho)
        b = ref.size_pools(data["trace"], meas, meas, data["slo"], rho)
        keep = ("P", "D", "decode_batch", "mean_prefill_s", "decode_step_s", "gpus")
        return {"available": True, "source": src, "l1_defaults": {k: a[k] for k in keep},
                "with_measured_efficiencies": {k: b[k] for k in keep},
                "assumed": {"mfu_prefill": base["mfu_prefill"], "hbm_eff": base["hbm_eff"]},
                "used": {"mfu_prefill": meas["mfu_prefill"], "hbm_eff": meas["hbm_eff"]}}
    except NotImplementedError as e:
        return {"available": False, "why": f"L1 starter not implemented yet ({e}); implement serve.py first"}


# ---------------------------------------------------------------------------------- invariants
def check(result: dict, env: dict) -> list[str]:
    fails = []
    pre, dec = result["tables"]["prefill"], result["tables"]["decode"]
    if any(r["median_s"] <= 0 for r in pre + dec):
        fails.append("non-positive latency: check the timer/synchronisation")
    # Prefill gets more efficient with length until compute-bound (small prompts are launch/latency-bound).
    if pre[-1]["tokens_per_s"] < pre[0]["tokens_per_s"]:
        fails.append(f"prefill throughput fell from {pre[0]['tokens_per_s']:.0f} to {pre[-1]['tokens_per_s']:.0f} tok/s as the "
                     "prompt grew: prefill should become compute-efficient with length; check for paging/OOM or clock throttling")
    gpu = env["device"] == "cuda"
    # Decode is memory-bound on a GPU: per-step time is roughly flat from batch 1 to batch 4-8. (On a CPU the
    # FLOP/byte ridge point is ~10x lower, so decode turns compute-bound at small batch: GPU-only invariant.)
    b1 = dec[0]["median_s"]
    mid = [r for r in dec if r["batch"] <= 8][-1]
    if gpu and mid["median_s"] > 1.6 * b1:
        fails.append(f"decode step at batch {mid['batch']} is {mid['median_s'] / b1:.2f}x batch 1: memory-bound decode should be "
                     "nearly flat in batch; check that weights are not re-copied per step and the KV slice is a view")
    # Tokens/s must grow with batch (that is the whole point of batching decode).
    if dec[-1]["tok_per_s"] <= dec[0]["tok_per_s"]:
        fails.append("decode tokens/s did not grow with batch: check the batched attention mask")
    f = result["fit_measured_ceiling"]
    # The fitted L1 model must explain the compute-bound prefill points and all decode points.
    bad_p = [p for p in f["pred_prefill"] if p["prompt_tokens"] in f["prefill_fit_points"] and abs(p["rel_err"]) > 0.30]
    bad_d = [p for p in f["pred_decode"] if abs(p["rel_err"]) > 0.35]
    if bad_p:
        fails.append(f"fitted prefill roofline misses T={[p['prompt_tokens'] for p in bad_p]} by > 30 %: the 2NT + 2LdT^2 model "
                     "does not describe this run; check for attention kernel fallbacks or throttling")
    if bad_d and gpu:
        fails.append(f"fitted decode model (bytes/(bw*eff) + overhead) misses batch {[p['batch'] for p in bad_d]} by > 35 %: check for GPU contention (another job on the GPU) or clock throttling")
    xc = result.get("l1_formula_crosscheck", {})
    if xc.get("available") and xc["max_rel_diff"] > 1e-6:
        fails.append(f"the L1 reference formulas disagree with this experiment's fit by {xc['max_rel_diff']:.1e}: "
                     "the FLOP/byte accounting here no longer matches serve.prefill_time_s / decode_step_time_s")
    if env["device"] == "cuda":
        vp = result.get("vendor_peaks", {})
        best = max(r["tflops_s"] for r in pre) * 1e12
        if vp.get("fp16_tc_flops") and best > 1.05 * vp["fp16_tc_flops"]:
            fails.append(f"prefill {best / 1e12:.1f} TFLOP/s exceeds the FP16 tensor peak {vp['fp16_tc_flops'] / 1e12:.1f}: "
                         "check the FLOP formula or the timer")
        top_bw = max(r["gbs"] for r in dec) * 1e9
        if vp.get("mem_bw") and top_bw > 1.10 * vp["mem_bw"]:
            fails.append(f"decode implies {top_bw / 1e9:.0f} GB/s, above the {vp['mem_bw'] / 1e9:.0f} GB/s memory peak: "
                         "weights must be sitting in L2 (model too small) or the byte count is wrong")
        if vp.get("mem_bw") and result["ceilings"]["copy_bytes_per_s"] > 1.05 * vp["mem_bw"]:
            fails.append("device copy bandwidth exceeds the memory peak: check the copy size (L2-resident?)")
        if result.get("fit_vendor_peak", {}).get("hbm_eff", 0) > 1.05:
            fails.append("fitted hbm_eff vs the vendor peak exceeds 1: impossible, check the decode byte count")
        for r in result["tables"]["kv_offload"]:
            g = (env.get("gpus") or [{}])[0]
            try:
                ceiling = {3: 0.985, 4: 1.969, 5: 3.938}[int(g["pcie.link.gen.max"])] * int(g["pcie.link.width.max"])
            except (KeyError, ValueError):
                ceiling = None
            if ceiling and r["gbs"] > 1.05 * ceiling:
                fails.append(f"KV offload {r['gbs']:.1f} GB/s exceeds the PCIe ceiling {ceiling:.1f} GB/s")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    md = result["model"]
    f = result["fit_measured_ceiling"]
    fv = result.get("fit_vendor_peak")
    L = ["## Model under test", "",
         f"Random-weight decoder: d={md['d']}, layers={md['layers']}, heads={md['heads']}, {md['dtype']}, "
         f"{md['params_nonembed'] / 1e6:.0f} M non-embedding parameters, {md['weight_bytes'] / 1e6:.0f} MB of weights, "
         f"{md['kv_bytes_per_token'] / 1024:.0f} KiB of KV per token.", "",
         f"Measured ceilings: dense GEMM **{result['ceilings']['gemm_flops'] / 1e12:.2f} TFLOP/s** (n={result['ceilings']['gemm_n']}), "
         f"memory copy **{result['ceilings']['copy_bytes_per_s'] / 1e9:.1f} GB/s** (read + write) `[MEASURED]`."]
    if gpu and result.get("vendor_peaks"):
        vp = result["vendor_peaks"]
        L.append(f"Vendor-class peaks at clocks.max.sm: FP16 tensor (FP32 accumulate) {vp.get('fp16_tc_flops', 0) / 1e12:.1f} TFLOP/s, "
                 f"memory {vp.get('mem_bw', 0) / 1e9:.0f} GB/s `[VENDOR-SPEC]` ({vp['source']}).")
    L += ["", "## Prefill (output length 1)", "", "| Prompt tokens | Median (ms) | p95 (ms) | IQR (ms) | TFLOP/s | tokens/s | L1 model (ms) | error |",
          "|---|---|---|---|---|---|---|---|"]
    pp = {p["prompt_tokens"]: p for p in f["pred_prefill"]}
    for r in result["tables"]["prefill"]:
        p = pp[r["prompt_tokens"]]
        L.append(f"| {r['prompt_tokens']} | {r['median_s'] * 1e3:.2f} | {r['p95_s'] * 1e3:.2f} | {r['iqr_s'] * 1e3:.3f} | "
                 f"{r['tflops_s']:.2f} | {r['tokens_per_s']:.0f} | {p['modeled_s'] * 1e3:.2f} | {p['rel_err'] * 100:+.0f} % |")
    L += ["", f"## Decode step at context {result['tables']['decode'][0]['ctx_tokens']}", "",
          "| Batch | Median (ms) | p95 (ms) | GB/s moved | tokens/s | L1 model (ms) | error |", "|---|---|---|---|---|---|---|"]
    pd_ = {p["batch"]: p for p in f["pred_decode"]}
    for r in result["tables"]["decode"]:
        p = pd_[r["batch"]]
        L.append(f"| {r['batch']} | {r['median_s'] * 1e3:.3f} | {r['p95_s'] * 1e3:.3f} | {r['gbs']:.1f} | {r['tok_per_s']:.0f} | "
                 f"{p['modeled_s'] * 1e3:.3f} | {p['rel_err'] * 100:+.0f} % |")
    L += ["", "## Fitted L1 constants", "", "| Constant | L1 default (H100-class TP8) | Fitted vs measured ceiling |"
          + (" Fitted vs vendor peak |" if fv else ""), "|---|---|---|" + ("---|" if fv else "")]
    for k, dflt in (("mfu_prefill", "0.5"), ("hbm_eff", "0.7"), ("step_overhead_s", "0.004 s")):
        fmt = (lambda v: f"{v * 1e3:.2f} ms") if k == "step_overhead_s" else (lambda v: f"{v:.2f}")
        L.append(f"| {k} | {dflt} | {fmt(f[k])} |" + (f" {fmt(fv[k])} |" if fv else ""))
    w = result.get("l1_sizing_whatif", {})
    if w.get("available"):
        a, b = w["l1_defaults"], w["with_measured_efficiencies"]
        L += ["", "## What-if: L1 pool sizing with the measured efficiencies `[MODELED]`", "",
              f"Using `{w['source']}` `size_pools()` for the H100-class instance, swapping mfu_prefill "
              f"{w['assumed']['mfu_prefill']} -> {w['used']['mfu_prefill']:.2f} and hbm_eff {w['assumed']['hbm_eff']} -> "
              f"{w['used']['hbm_eff']:.2f}:", "", "| | P (prefill) | D (decode) | decode batch | GPUs |", "|---|---|---|---|---|",
              f"| L1 defaults | {a['P']} | {a['D']} | {a['decode_batch']} | {a['gpus']} |",
              f"| measured efficiencies | {b['P']} | {b['D']} | {b['decode_batch']} | {b['gpus']} |", "",
              "_This transfers efficiencies measured on a small model on a laptop GPU onto a 70B TP8 H100-class instance. "
              "Constants are relative to the vendor peak, as the L1 hardware table is. It shows how sensitive the pool sizes are to these constants; it is not a prediction for ORION._"]
    elif w:
        L += ["", f"L1 what-if skipped: {w.get('why')}"]
    xc = result.get("l1_formula_crosscheck", {})
    if xc.get("available"):
        L += ["", f"The L1 formulas in `{xc['source']}` (`prefill_time_s`, `decode_step_time_s`, MODEL re-pointed at this model) "
              f"reproduce the 'L1 model' columns to {xc['max_rel_diff']:.0e} relative difference."]
    kv = result["tables"]["kv_offload"]
    L += ["", "## KV transfer path available on one host", "", "| Prompt tokens | KV bytes | Median (ms) | GB/s | path |", "|---|---|---|---|---|"]
    for r in kv:
        L.append(f"| {r['prompt_tokens']} | {r['kv_bytes'] / 1e6:.1f} MB | {r['median_s'] * 1e3:.3f} | {r['gbs']:.1f} | {r['path']} |")
    nr = result["not_runnable_parts"][0]
    L += ["", "## Not runnable here", "", f"- **{nr['part']}**. Probe: {nr['probe']}. Needs: {', '.join(nr['needs'])}. "
          f"Fallback: {nr['fallback']}."]
    L += ["", "## What to conclude", ""]
    if gpu:
        L += [f"- This is a **laptop Ada GPU (RTX 4060 class), not an H100**: absolute times are not ORION evidence. The *shape* is: "
              "prefill throughput rises with prompt length until it is compute-bound, and decode step time stays nearly "
              "flat across small batches because every step streams all the weights.",
              f"- Decode step overhead (~{f['step_overhead_s'] * 1e3:.2f} ms here) is mostly per-kernel launch cost from an eager "
              "Python loop; serving stacks hide it with CUDA graphs. It is the same term the L1 model calls `step_overhead_s`.",
              "- Feed the fitted constants, not the defaults, into the capacity model, and refit on the target GPU and serving stack."]
    else:
        ridge = result["ceilings"]["gemm_flops"] / result["ceilings"]["copy_bytes_per_s"]
        L += ["- _CPU fallback: no GPU was used. mfu_prefill and hbm_eff are relative to a GEMM and a copy measured on this CPU, "
              "and the GPU-only invariants (vendor peak, memory peak, PCIe ceiling, flat memory-bound decode, decode-model "
              "agreement) were skipped._",
              f"- This CPU's ridge point is ~{ridge:.0f} FLOP/byte (a GPU's is in the hundreds), so decode becomes compute-bound "
              "at small batches here and the memory-only L1 decode formula fits poorly: exactly why the L1 model is a GPU model.",
              "- The prefill/decode asymmetry still shows: prefill throughput grows with prompt length, decode tokens/s grows with batch."]
    return "\n".join(L)
