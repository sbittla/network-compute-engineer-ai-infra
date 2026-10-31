"""Ch 15 L2: prefill vs decode, TTFT/ITL and KV cache memory of a small random-weight transformer on one GPU,
compared with the lab's capacity model (Part A).

What it teaches (Sections 15.2-15.5): prefill is compute-bound (time grows with prompt length, high
TFLOP/s), decode is memory-bandwidth-bound (every step streams all weights once, so per-step time is
almost flat in batch size and throughput grows with batch until the KV reads or compute catch up), and
the KV cache is sized exactly by ``2 x layers x kv_heads x head_dim x bytes`` per token. The lab's
``decode_step_time_s`` is a lower bound when ``hbm_efficiency = 1`` and ``overhead = 0``; this run backs
out the real efficiency and per-step overhead of an eager PyTorch decode loop. A serving engine
(vLLM, SGLang, TensorRT-LLM) and a real open model are what the README's L2 asks for; neither can be
downloaded here (no network), so a GQA decoder with random weights and the same shapes-to-bytes
arithmetic stands in. It is not an engine benchmark: no continuous batching, paged attention or CUDA
graphs.

Measured (GPU, BF16):
1. KV cache bytes per token: allocator delta of a preallocated cache vs ``kv_bytes_per_token``.
2. Prefill latency vs prompt length (batch 1), achieved TFLOP/s and the implied ``prefill_mfu``.
3. Decode step time vs batch at a fixed context; implied ``hbm_efficiency`` and fixed overhead from a
   linear fit of step time against bytes moved; tokens/s vs batch.
4. A generation loop (batch of requests, fixed prompt, fixed output length, >= 5 runs): TTFT, ITL
   p50/p95/p99 and TPOT, against the lab model's prediction for the same shapes.
5. The lab's capacity model for this GPU: KV budget and max concurrent sequences with the measured
   weight bytes and activation reserve.

CPU fallback: the same experiment with a smaller FP32 model on the CPU (KV bytes counted from tensor
sizes; DRAM-bandwidth and device-peak bounds skipped; the efficiency fit uses a nominal CPU DRAM rate).
"""
from __future__ import annotations

import importlib.util
import math
import statistics
import time
from pathlib import Path

EXPERIMENT = {
    "id": "ch15-l2",
    "title": "Lab 15 L2: prefill vs decode, TTFT/ITL and KV cache memory vs the capacity model",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same random-weight GQA decoder, smaller and in FP32, runs prefill/decode/generation on the "
                     "CPU; KV bytes are counted from tensor sizes and GPU bandwidth/peak invariants are skipped"),
}

PKG = Path(__file__).resolve().parents[2]
ADA_BF16_FLOP_PER_CLK_SM = 512        # NVIDIA Ada whitepaper (RTX 4090 165.2 TFLOP/s dense BF16, 128 SMs, 2520 MHz)
BUS_WIDTH_BITS = {"RTX 4060 Laptop": 128, "RTX 4090": 384}
CPU_NOMINAL_DRAM_GBS = 60.0           # ILLUSTRATIVE dual-channel DDR5 figure, used only to express CPU efficiency
LAB_HBM_EFFICIENCY, LAB_OVERHEAD_S, LAB_PREFILL_MFU = 0.70, 0.003, 0.40     # data/configs.yaml (ILLUSTRATIVE)


# ------------------------------------------------------------------------------------- lab model
def lab_model():
    """The lab's Part A functions: reference solution if present, else the learner's starter, else the
    Section 15 formulas inline (so the run also works in the learner release before Part A is done)."""
    for path in (PKG / "solutions" / "lab" / "serving_lab.py", PKG / "lab" / "starter" / "serving_lab.py"):
        if path.is_file():
            spec = importlib.util.spec_from_file_location(f"serving_lab_{path.parent.name}", path)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                mod.kv_bytes_per_token(1, 1, 1, 2)
                return mod, path.relative_to(PKG).as_posix()
            except Exception:  # starter not implemented yet
                continue

    class Inline:
        @staticmethod
        def kv_bytes_per_token(n_layers, n_kv_heads, head_dim, bytes_per_elem):
            return int(round(2 * n_layers * n_kv_heads * head_dim * bytes_per_elem))

        @staticmethod
        def kv_budget_bytes(n_gpus, hbm, frac, weight_bytes, reserve):
            return max(0.0, n_gpus * hbm * frac - weight_bytes - n_gpus * reserve)

        @staticmethod
        def max_concurrent_sequences(budget, kvpt, seq_tokens, block_tokens=16):
            return int(budget // (block_tokens * kvpt)) // math.ceil(seq_tokens / block_tokens)

        @staticmethod
        def prefill_time_s(n_params, prompt, n_gpus, peak, mfu):
            return 2.0 * n_params * prompt / (n_gpus * peak * mfu)

        @staticmethod
        def decode_step_time_s(w, batch, ctx, kvpt, n_gpus, bw, eff=1.0, overhead=0.0):
            return overhead + (w + batch * ctx * kvpt) / (n_gpus * bw * eff)
    return Inline, "inline Section 15 formulas"


# ------------------------------------------------------------------------------------------ model
def make_model(torch, cfg: dict, device: str, dtype):
    g = torch.Generator(device="cpu").manual_seed(0)
    h, L, nh, kvh, d, ff, V = (cfg[k] for k in ("h", "layers", "heads", "kv_heads", "head_dim", "ffn", "vocab"))

    def w(*shape):
        return (torch.randn(*shape, generator=g) / math.sqrt(shape[-1])).to(device=device, dtype=dtype)
    layers = [{"ln1": torch.ones(h, device=device, dtype=dtype), "ln2": torch.ones(h, device=device, dtype=dtype),
               "wq": w(nh * d, h), "wkv": w(2 * kvh * d, h), "wo": w(h, nh * d),
               "w_gate_up": w(2 * ff, h), "w_down": w(h, ff)} for _ in range(L)]
    return {"emb": w(V, h), "layers": layers, "ln_f": torch.ones(h, device=device, dtype=dtype), "head": w(V, h)}


def n_params(model) -> int:
    n = model["emb"].numel() + model["head"].numel() + model["ln_f"].numel()
    return n + sum(t.numel() for lyr in model["layers"] for t in lyr.values())


def forward(torch, model, cfg, tokens, cache_k, cache_v, pos: int):
    """tokens [B, T] starting at position ``pos``; writes K/V into the preallocated caches; returns the
    logits of the last position [B, V]."""
    F = torch.nn.functional
    B, T = tokens.shape
    nh, kvh, d = cfg["heads"], cfg["kv_heads"], cfg["head_dim"]
    x = model["emb"][tokens]
    for i, lyr in enumerate(model["layers"]):
        a = F.rms_norm(x, (x.shape[-1],), lyr["ln1"])
        q = (a @ lyr["wq"].T).view(B, T, nh, d).transpose(1, 2)
        kv = (a @ lyr["wkv"].T).view(B, T, 2, kvh, d)
        cache_k[i][:, :, pos:pos + T] = kv[:, :, 0].transpose(1, 2)
        cache_v[i][:, :, pos:pos + T] = kv[:, :, 1].transpose(1, 2)
        k, v = cache_k[i][:, :, :pos + T], cache_v[i][:, :, :pos + T]
        if T == 1:
            # decode: fold the query heads of each KV group into the query-length axis -> no K/V replication
            o = F.scaled_dot_product_attention(q.reshape(B, kvh, nh // kvh, d), k, v)
            o = o.reshape(B, nh, 1, d)
        else:
            try:
                o = F.scaled_dot_product_attention(q, k, v, is_causal=pos == 0, enable_gqa=True)
            except TypeError:  # torch < 2.5
                rep = nh // kvh
                o = F.scaled_dot_product_attention(q, k.repeat_interleave(rep, 1), v.repeat_interleave(rep, 1),
                                                   is_causal=pos == 0)
        x = x + o.transpose(1, 2).reshape(B, T, nh * d) @ lyr["wo"].T
        m = F.rms_norm(x, (x.shape[-1],), lyr["ln2"])
        gate, up = (m @ lyr["w_gate_up"].T).chunk(2, dim=-1)
        x = x + (F.silu(gate) * up) @ lyr["w_down"].T
    return F.rms_norm(x[:, -1], (x.shape[-1],), model["ln_f"]) @ model["head"].T


def alloc_cache(torch, cfg, B: int, max_len: int, device: str, dtype):
    shape = (B, cfg["kv_heads"], max_len, cfg["head_dim"])
    return ([torch.empty(shape, device=device, dtype=dtype) for _ in range(cfg["layers"])],
            [torch.empty(shape, device=device, dtype=dtype) for _ in range(cfg["layers"])])


# ------------------------------------------------------------------------------------------- peaks
def gpu_peaks(env: dict) -> dict:
    g0, g = env.get("gpu0", {}), (env.get("gpus") or [{}])[0]
    out = {"flops": None, "dram_Bps": None, "src": ""}
    try:
        if g0.get("capability") == "8.9":
            out["flops"] = ADA_BF16_FLOP_PER_CLK_SM * g0["sm_count"] * float(g["clocks.max.sm"]) * 1e6
        for key, width in BUS_WIDTH_BITS.items():
            if key in g0.get("name", ""):
                out["dram_Bps"] = float(g["clocks.max.memory"]) * 1e6 * 2 * width / 8
        out["src"] = (f"BF16 512 FLOP/clk/SM x {g0.get('sm_count')} SMs x {g.get('clocks.max.sm')} MHz (Ada whitepaper); "
                      f"DRAM {g.get('clocks.max.memory')} MHz x 2 x bus width (NVIDIA spec)")
    except (KeyError, ValueError, TypeError):
        pass
    return out


# --------------------------------------------------------------------------------------------- run
def run(ctx) -> dict:
    torch = ctx.torch
    gpu = ctx.is_gpu
    dev = ctx.device
    if gpu:
        dtype, elem = torch.bfloat16, 2
        cfg = {"layers": 4 if ctx.quick else 12, "h": 2048, "heads": 16, "kv_heads": 4, "head_dim": 128,
               "ffn": 5632, "vocab": 32000}
        prompts = [128, 512] if ctx.quick else [128, 512, 1024, 2048]
        batches = [1, 4, 16] if ctx.quick else [1, 2, 4, 8, 16, 32]
        ctx_len, gen_batch, gen_prompt, gen_out = 512, 8, 512, (16 if ctx.quick else 64)
        ctx_sweep_batch, ctx_sweep = 8, ([2048] if ctx.quick else [1024, 2048, 4096])
    else:
        torch.set_num_threads(max(1, min(8, torch.get_num_threads())))
        dtype, elem = torch.float32, 4
        cfg = {"layers": 2 if ctx.quick else 4, "h": 512, "heads": 8, "kv_heads": 2, "head_dim": 64,
               "ffn": 1408, "vocab": 8000}
        prompts = [64, 256] if ctx.quick else [64, 256, 512]
        batches = [1, 4, 16] if ctx.quick else [1, 4, 8, 16]
        ctx_len, gen_batch, gen_prompt, gen_out = 256, 4, 128, (16 if ctx.quick else 32)
        ctx_sweep_batch, ctx_sweep = 4, ([1024] if ctx.quick else [1024, 2048])
    lab, lab_src = lab_model()
    reps = ctx.reps(5)

    with torch.inference_mode():
        if gpu:
            torch.cuda.empty_cache()
            m0 = torch.cuda.memory_allocated()
        model = make_model(torch, cfg, dev, dtype)
        N = n_params(model)
        weight_bytes = N * elem
        if gpu:
            ctx.sync()
            weight_alloc = torch.cuda.memory_allocated() - m0
        kvpt_model = lab.kv_bytes_per_token(cfg["layers"], cfg["kv_heads"], cfg["head_dim"], elem)
        ctx.log(f"model {N / 1e6:.0f} M params ({weight_bytes / 1e9:.2f} GB {str(dtype).split('.')[-1]}), "
                f"KV {kvpt_model} B/token [MODELED]")

        # 1. KV cache bytes per token: allocate a cache and measure it
        Bk, Lk = 8, 1024
        if gpu:
            a0 = torch.cuda.memory_allocated()
        ck, cv = alloc_cache(torch, cfg, Bk, Lk, dev, dtype)
        kv_measured = ((torch.cuda.memory_allocated() - a0) if gpu
                       else sum(t.numel() * t.element_size() for t in ck + cv)) / (Bk * Lk)
        del ck, cv

        # 2. prefill latency vs prompt length (batch 1): TTFT without queueing
        pre_rows = []
        for P in prompts:
            ck, cv = alloc_cache(torch, cfg, 1, P + 1, dev, dtype)
            toks = torch.randint(0, cfg["vocab"], (1, P), device=dev)
            if gpu:
                torch.cuda.reset_peak_memory_stats()
                base = torch.cuda.memory_allocated()
            st = ctx.bench(lambda: forward(torch, model, cfg, toks, ck, cv, 0).argmax(-1), warmup=2, reps=reps)
            act_peak = (torch.cuda.max_memory_allocated() - base) if gpu else None
            flops = 2 * N * P + 4 * cfg["layers"] * cfg["heads"] * cfg["head_dim"] * P * P / 2   # matmuls + causal attn
            pre_rows.append({"prompt": P, "median_s": st["median"], "p95_s": st["p95"], "iqr_s": st["iqr"],
                             "min_s": st["min"],
                             "n": st["n"], "tflops": flops / st["median"] / 1e12, "flops": flops,
                             "activation_peak_bytes": act_peak})
            del ck, cv
            ctx.log(f"prefill P={P}: {st['median'] * 1e3:.2f} ms, {flops / st['median'] / 1e12:.2f} TFLOP/s")

        # 3. decode step time vs batch at a fixed context, then vs context at a fixed batch (KV reads grow)
        dec_rows = []
        for B, C in [(b, ctx_len) for b in batches] + [(ctx_sweep_batch, c) for c in ctx_sweep]:
            ck, cv = alloc_cache(torch, cfg, B, C + 1, dev, dtype)
            for t in ck + cv:
                t.normal_()
            tok = torch.randint(0, cfg["vocab"], (B, 1), device=dev)
            st = ctx.bench(lambda: forward(torch, model, cfg, tok, ck, cv, C).argmax(-1), warmup=3,
                           reps=ctx.reps(20))
            bytes_moved = weight_bytes + B * C * kvpt_model
            dec_rows.append({"batch": B, "context": C, "sweep": "batch" if C == ctx_len else "context", "median_s": st["median"], "p95_s": st["p95"],
                             "iqr_s": st["iqr"], "min_s": st["min"], "n": st["n"], "bytes_moved": bytes_moved,
                             "tokens_per_s": B / st["median"], "eff_GBps": bytes_moved / st["median"] / 1e9})
            del ck, cv
            ctx.log(f"decode B={B} ctx={C}: {st['median'] * 1e3:.2f} ms/step, {B / st['median']:.0f} tok/s, "
                    f"{bytes_moved / st['median'] / 1e9:.1f} GB/s effective")

        # 4. generation loop: TTFT, ITL, TPOT
        ttft, itl, tpot = [], [], []
        for r in range(1 + reps):
            ck, cv = alloc_cache(torch, cfg, gen_batch, gen_prompt + gen_out + 1, dev, dtype)
            prompt = torch.randint(0, cfg["vocab"], (gen_batch, gen_prompt), device=dev)
            ctx.sync()
            t0 = time.perf_counter()
            nxt = forward(torch, model, cfg, prompt, ck, cv, 0).argmax(-1, keepdim=True)
            ctx.sync()
            t_first = time.perf_counter()
            gaps, last = [], t_first
            for i in range(gen_out - 1):
                nxt = forward(torch, model, cfg, nxt, ck, cv, gen_prompt + i).argmax(-1, keepdim=True)
                ctx.sync()
                now = time.perf_counter()
                gaps.append(now - last)
                last = now
            del ck, cv
            if r == 0:
                continue          # warm-up run
            ttft.append(t_first - t0)
            itl.extend(gaps)
            tpot.append((last - t_first) / (gen_out - 1))
        peak_alloc = torch.cuda.max_memory_allocated() if gpu else None

    import hwlab
    gen = {"batch": gen_batch, "prompt": gen_prompt, "output": gen_out, "runs": reps,
           "ttft": hwlab.summarize(ttft), "tpot": hwlab.summarize(tpot), "itl": hwlab.summarize(itl),
           "itl_p99_s": sorted(itl)[min(len(itl) - 1, round(0.99 * (len(itl) - 1)))]}
    # linear fit of decode step time against bytes moved: t = overhead + bytes / (bw_eff)
    # fitted on the best-of-n step times (the uncontended cost; robust to GPU time-slicing with other tenants)
    xs, ys = [r["bytes_moved"] for r in dec_rows], [r["min_s"] for r in dec_rows]
    if len(set(xs)) > 1:
        mx, my = statistics.fmean(xs), statistics.fmean(ys)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        intercept = my - slope * mx
    else:
        slope, intercept = float("nan"), float("nan")
    return {"metrics": {
        "model": cfg, "dtype": str(dtype).split(".")[-1], "n_params": N, "weight_bytes": weight_bytes,
        "weight_alloc_bytes": weight_alloc if gpu else None,
        "kv_bytes_per_token_model": kvpt_model, "kv_bytes_per_token_measured": kv_measured,
        "decode_fit_overhead_s": intercept, "decode_fit_GBps": (1 / slope / 1e9) if slope and slope > 0 else None,
        "ttft_p50_s": gen["ttft"]["median"], "ttft_p95_s": gen["ttft"]["p95"],
        "itl_p50_s": gen["itl"]["median"], "itl_p95_s": gen["itl"]["p95"], "itl_p99_s": gen["itl_p99_s"],
        "tpot_p50_s": gen["tpot"]["median"], "peak_alloc_bytes": peak_alloc,
        "activation_reserve_bytes": max((r["activation_peak_bytes"] or 0) for r in pre_rows) if gpu else None,
        "lab_model_source": lab_src,
    }, "tables": {"prefill": pre_rows, "decode": dec_rows}, "generation": gen, "notes": [
        "Model: random-weight GQA decoder (RMSNorm, SwiGLU MLP, untied embedding/LM head), no tokenizer or download; "
        "greedy argmax sampling. Latency depends only on shapes, so random weights measure the same thing a real "
        "checkpoint of these shapes would.",
        f"Benchmark: prefill {reps} reps after 2 warm-ups, decode {ctx.reps(20)} reps after 3 warm-ups (CUDA events "
        f"on the GPU); generation: 1 warm-up run then {reps} runs, every step synchronised (what a client sees).",
        "Eager PyTorch, no CUDA graphs, no paged attention, no continuous batching: the per-step overhead measured "
        "here is Python + kernel-launch cost that engines remove; do not read it as vLLM's overhead.",
        f"Lab model: {lab_src}.",
        "Not runnable here: the README's L2 serving-engine benchmark (vLLM/SGLang with an open 7-8B model; needs the "
        "network to fetch the engine and weights, and > 8 GB for BF16 7B weights + KV) and the L3 disaggregated "
        "prefill/decode over RDMA (needs 2+ nodes with RDMA NICs).",
    ] + ([] if gpu else ["CPU fallback: FP32 on host memory; GPU bandwidth and peak invariants were skipped, and "
                         f"efficiencies are expressed against a nominal {CPU_NOMINAL_DRAM_GBS:.0f} GB/s DRAM rate "
                         "[ILLUSTRATIVE]."])}


def _predictions(result: dict, env: dict) -> dict:
    m = result["metrics"]
    lab, _ = lab_model()
    gpu = env["device"] == "cuda"
    pk = gpu_peaks(env) if gpu else {"flops": None, "dram_Bps": CPU_NOMINAL_DRAM_GBS * 1e9}
    gen = result["generation"]
    out = {"peaks": pk}
    if pk["dram_Bps"]:
        bw = pk["dram_Bps"]
        dec = result["tables"]["decode"]
        out["decode_lower_bound_s"] = {(r["batch"], r["context"]): lab.decode_step_time_s(
            m["weight_bytes"], r["batch"], r["context"], m["kv_bytes_per_token_model"], 1, bw, 1.0, 0.0) for r in dec}
        out["hbm_efficiency"] = {(r["batch"], r["context"]): out["decode_lower_bound_s"][(r["batch"], r["context"])]
                                 / r["median_s"] for r in dec}
        out["hbm_efficiency_best"] = {(r["batch"], r["context"]): out["decode_lower_bound_s"][(r["batch"], r["context"])]
                                      / r["min_s"] for r in dec}
        ctx_avg = gen["prompt"] + gen["output"] / 2
        out["tpot_lab_default_s"] = lab.decode_step_time_s(m["weight_bytes"], gen["batch"], ctx_avg,
                                                           m["kv_bytes_per_token_model"], 1, bw,
                                                           LAB_HBM_EFFICIENCY, LAB_OVERHEAD_S)
    if pk["flops"]:
        out["prefill_mfu"] = {r["prompt"]: lab.prefill_time_s(m["n_params"], r["prompt"], 1, pk["flops"], 1.0) / r["median_s"]
                              for r in result["tables"]["prefill"]}
        out["ttft_lab_default_s"] = lab.prefill_time_s(m["n_params"], gen["prompt"] * gen["batch"], 1, pk["flops"],
                                                       LAB_PREFILL_MFU)
    if gpu:
        total = env.get("gpu0", {}).get("total_memory_gib", 8) * 1024 ** 3
        reserve = m["activation_reserve_bytes"] or 0
        budget = lab.kv_budget_bytes(1, total, 0.90, m["weight_bytes"], reserve)
        out["capacity"] = {"hbm_bytes": total, "mem_fraction": 0.90, "reserve_bytes": reserve, "kv_budget_bytes": budget,
                           "max_seqs_4096": lab.max_concurrent_sequences(budget, m["kv_bytes_per_token_model"], 4096, 16),
                           "max_seqs_1024": lab.max_concurrent_sequences(budget, m["kv_bytes_per_token_model"], 1024, 16)}
    return out


def check(result: dict, env: dict) -> list[str]:
    m, t = result["metrics"], result["tables"]
    gpu = env["device"] == "cuda"
    p = _predictions(result, env)
    fails = []
    kv_m, kv_p = m["kv_bytes_per_token_measured"], m["kv_bytes_per_token_model"]
    if abs(kv_m - kv_p) > 0.01 * kv_p:
        fails.append(f"KV cache {kv_m:.0f} B/token vs model {kv_p} B/token (> 1 %): the cache stores the wrong number "
                     "of heads (GQA: kv_heads, not query heads) or the wrong dtype")
    pre = t["prefill"]
    if not all(b["min_s"] > a["min_s"] for a, b in zip(pre, pre[1:])):
        fails.append("prefill time did not grow with prompt length: the prefill is not doing per-token work")
    # best-of-n step times for the physical checks (robust to time-slicing with other GPU tenants)
    dec = [r for r in t["decode"] if r["sweep"] == "batch"]
    if not all(b["batch"] / b["min_s"] > a["batch"] / a["min_s"] for a, b in zip(dec, dec[1:])):
        fails.append("decode tokens/s did not grow with batch: the step is not weight-bandwidth-bound; check for a "
                     "per-sequence loop or a shared/throttled device")
    b1 = dec[0]
    b16 = next((r for r in dec if r["batch"] == 16), dec[-1])
    if gpu and b16["min_s"] > 2.0 * b1["min_s"]:
        fails.append(f"decode step at batch {b16['batch']} is {b16['min_s'] / b1['min_s']:.1f} x batch 1 (> 2 x): "
                     "while memory-bound the per-step latency should stay roughly flat")
    sweep_b = t["decode"][-1]["batch"]
    cs = sorted((r for r in t["decode"] if r["batch"] == sweep_b), key=lambda r: r["context"])
    if gpu and len(cs) >= 2 and not cs[-1]["min_s"] > cs[0]["min_s"]:
        fails.append("decode step time did not grow with context: the KV cache is not being read (check the "
                     "attention slice cache[:, :, :pos+1])")
    if not m["ttft_p50_s"] > m["itl_p50_s"]:
        fails.append("TTFT p50 <= ITL p50: the prefill of a batch of prompts should cost more than one decode step")
    if gpu:
        for b, eff in p.get("hbm_efficiency_best", {}).items():
            if eff > 1.05:
                fails.append(f"decode at (batch, context) {b} moved bytes faster than DRAM peak (efficiency {eff:.2f}): check the "
                             "byte count or the peak table")
        for P, mfu in p.get("prefill_mfu", {}).items():
            if mfu > 1.05:
                fails.append(f"prefill P={P} exceeds the device BF16 peak (MFU {mfu:.2f}): check the FLOP count")
        if m["peak_alloc_bytes"] and m["peak_alloc_bytes"] > 5e9:
            fails.append("experiment used > 5 GB of VRAM; reduce layers or batch")
        if m["weight_alloc_bytes"] and abs(m["weight_alloc_bytes"] - m["weight_bytes"]) > 0.02 * m["weight_bytes"]:
            fails.append("allocated weight bytes differ from params x 2 B by > 2 %: dtype is not BF16")
    return fails


def report(result: dict, env: dict) -> str:
    m, t, gen = result["metrics"], result["tables"], result["generation"]
    gpu = env["device"] == "cuda"
    p = _predictions(result, env)
    c = m["model"]
    lines = [f"Model: {c['layers']} layers, h={c['h']}, {c['heads']} query / {c['kv_heads']} KV heads x {c['head_dim']}, "
             f"SwiGLU {c['ffn']}, vocab {c['vocab']}: **{m['n_params'] / 1e6:.0f} M params, "
             f"{m['weight_bytes'] / 1e9:.2f} GB {m['dtype']}**. Lab model: {m['lab_model_source']}.", "",
             "## KV cache", "",
             f"Measured **{m['kv_bytes_per_token_measured']:.0f} B/token** vs `kv_bytes_per_token` = 2 x {c['layers']} x "
             f"{c['kv_heads']} x {c['head_dim']} x {2 if gpu else 4} = **{m['kv_bytes_per_token_model']} B/token** "
             f"`[MODELED]`. Full multi-head KV would be {c['heads'] // c['kv_heads']} x larger.", ""]
    if "capacity" in p:
        cap = p["capacity"]
        lines += [f"Capacity model for this GPU (`kv_budget_bytes`, `max_concurrent_sequences`): "
                  f"{cap['hbm_bytes'] / 2**30:.1f} GiB x 0.90 - weights {m['weight_bytes'] / 1e9:.2f} GB - measured "
                  f"activation reserve {cap['reserve_bytes'] / 1e6:.0f} MB = **{cap['kv_budget_bytes'] / 1e9:.2f} GB** of KV "
                  f"-> {cap['max_seqs_4096']} sequences of 4,096 tokens, {cap['max_seqs_1024']} of 1,024 `[MODELED]`.", ""]
    lines += ["## Prefill (batch 1): compute-bound", "",
              "| Prompt tokens | Median (ms) | p95 (ms) | IQR (ms) | TFLOP/s | Implied MFU |", "|---|---|---|---|---|---|"]
    for r in t["prefill"]:
        mfu = p.get("prefill_mfu", {}).get(r["prompt"])
        lines.append(f"| {r['prompt']} | {r['median_s'] * 1e3:.2f} | {r['p95_s'] * 1e3:.2f} | {r['iqr_s'] * 1e3:.2f} | "
                     f"{r['tflops']:.2f} | {f'{mfu:.2f}' if mfu else 'n/a'} |")
    lines += ["", "## Decode: memory-bound (batch sweep at fixed context, then context sweep at fixed batch)", "",
              "| Batch | Context | Step median (ms) | p95 (ms) | tokens/s | Effective GB/s | Lab lower bound (ms) | Implied hbm_efficiency |",
              "|---|---|---|---|---|---|---|---|"]
    for r in t["decode"]:
        lb = p.get("decode_lower_bound_s", {}).get((r["batch"], r["context"]))
        eff = p.get("hbm_efficiency", {}).get((r["batch"], r["context"]))
        lines.append(f"| {r['batch']} | {r['context']} | {r['median_s'] * 1e3:.2f} | {r['p95_s'] * 1e3:.2f} | {r['tokens_per_s']:.0f} | "
                     f"{r['eff_GBps']:.1f} | {lb * 1e3:.2f} | {eff:.2f} |" if lb else
                     f"| {r['batch']} | {r['context']} | {r['median_s'] * 1e3:.2f} | {r['p95_s'] * 1e3:.2f} | {r['tokens_per_s']:.0f} | "
                     f"{r['eff_GBps']:.1f} | n/a | n/a |")
    if m["decode_fit_GBps"] and m["decode_fit_overhead_s"] >= 0:
        lines += ["", f"Fit t = overhead + bytes / B over both sweeps (best-of-n step times): overhead **{m['decode_fit_overhead_s'] * 1e3:.2f} ms**, "
                  f"B = **{m['decode_fit_GBps']:.0f} GB/s** (lab assumes `step_overhead_s` = 3 ms, `hbm_efficiency` = 0.70)."]
    else:
        lines += ["", "Fit t = overhead + bytes / B: **not meaningful in this run** (negative or undefined intercept). Step "
                  "time was not linear in bytes moved: either the device was shared (time-slicing noise) or the step is "
                  "compute/launch-bound rather than bandwidth-bound" + (" (expected for this small FP32 model on a CPU)."
                                                                         if not gpu else ". Rerun on an idle GPU.")]
    lines += ["", f"## Generation: batch {gen['batch']}, prompt {gen['prompt']}, {gen['output']} output tokens, {gen['runs']} runs", "",
              "| Metric | p50 (ms) | p95 (ms) | p99 (ms) | n |", "|---|---|---|---|---|",
              f"| TTFT | {gen['ttft']['median'] * 1e3:.2f} | {gen['ttft']['p95'] * 1e3:.2f} | - | {gen['ttft']['n']} |",
              f"| ITL | {gen['itl']['median'] * 1e3:.2f} | {gen['itl']['p95'] * 1e3:.2f} | {gen['itl_p99_s'] * 1e3:.2f} | {gen['itl']['n']} |",
              f"| TPOT (per run) | {gen['tpot']['median'] * 1e3:.2f} | {gen['tpot']['p95'] * 1e3:.2f} | - | {gen['tpot']['n']} |"]
    if "tpot_lab_default_s" in p:
        lines += ["", f"Lab model with its default ILLUSTRATIVE parameters (`hbm_efficiency` 0.70, 3 ms overhead) and this "
                  f"device's {'DRAM peak' if gpu else 'nominal DRAM rate'}: TPOT **{p['tpot_lab_default_s'] * 1e3:.2f} ms** "
                  f"vs measured {gen['tpot']['median'] * 1e3:.2f} ms."
                  + (f" Prefill of the batch at `prefill_mfu` 0.40: TTFT **{p['ttft_lab_default_s'] * 1e3:.1f} ms** vs "
                     f"measured {gen['ttft']['median'] * 1e3:.1f} ms." if "ttft_lab_default_s" in p else "")]
    if gpu and p["peaks"].get("src"):
        lines += ["", f"Device peaks `[VENDOR-SPEC]`: {p['peaks']['flops'] / 1e12:.1f} TFLOP/s BF16, "
                  f"{p['peaks']['dram_Bps'] / 1e9:.0f} GB/s DRAM ({p['peaks']['src']})."]
    lines += ["", "## What to conclude", "",
              "- Prefill time scales with prompt length at high TFLOP/s; decode step time barely moves with batch while "
              "tokens/s scales almost linearly: batch is the decode throughput lever, and the KV cache is what limits it.",
              "- The KV formula is exact; the capacity model's uncertainty is in the reserve and fragmentation, not in "
              "bytes per token. Measure the reserve, as done here.",
              "- The measured hbm_efficiency and overhead replace the lab's ILLUSTRATIVE 0.70 / 3 ms only for this stack "
              "(eager PyTorch). Record them in the manifest; do not copy them into configs.yaml as 'validated'.",
              "- ITL p99 above p50 is launch and scheduling jitter on an unloaded single request stream; under real "
              "load the scheduler's prefill interruptions dominate it (Section 15.6)."]
    if gpu:
        lines += ["", "_Laptop RTX 4060 (8 GB GDDR6, ~256 GB/s), not an H100 (80 GB HBM3, 3.35 TB/s): ratios and shapes "
                  "transfer, absolute latencies do not._"]
    else:
        lines += ["", "_CPU fallback: no GPU was used. Bandwidth/peak invariants were skipped; efficiencies are against an "
                  "ILLUSTRATIVE DRAM figure._"]
    return "\n".join(lines)
