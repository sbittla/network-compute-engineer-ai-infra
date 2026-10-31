"""Capstone D L2: replay a scaled W-INFER trace through a real continuous-batching engine on one GPU.

What it teaches (starter-kit README section 8; manuscript Ch 19 serving, Ch 18/20 SLOs): TTFT, TPOT,
ITL and goodput are properties of the *engine and its configuration* under a given arrival process,
not of the model alone. A small randomly initialised decoder-only transformer (no download, no
network) is served by a minimal vLLM-like engine (FIFO admission up to ``max_num_seqs``, whole-prompt
prefill, one batched decode step per iteration over every running sequence, KV cache in fixed slots).
The same scaled slice of ``data/trace_s1.csv`` is replayed in real time under two configurations
(small vs large ``max_num_seqs``), per-request latencies are measured, the L1 SLI definitions
(``serving.summarize``) are applied to the measured requests, and the L1 simulator
(``serving.simulate``) is run on the identical trace with this GPU's measured ceilings so measured
and simulated percentiles can be compared and the gap explained.

Not runnable on one host: a supported serving stack with an open model (no model download, network
off), TP=8 on an HX8 node, and the L3 multi-replica routing / canary drill. Probed and recorded.

CPU fallback: the same engine and trace on the CPU with a smaller fp32 model and an arrival
rate sized for the CPU; the GPU-only invariants (flat memory-bound decode, memory peak) are skipped.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import statistics
import sys
import time
from pathlib import Path

EXPERIMENT = {
    "id": "capstone-d-l2",
    "title": "Capstone D L2: continuous-batching serving latency and goodput on one GPU",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same engine replays the same trace slice on the CPU with a smaller fp32 random-weight model "
                     "(arrival compression sized for the CPU); TTFT/TPOT/goodput are CPU measurements and the simulator is "
                     "calibrated to measured CPU ceilings"),
}

PKG = Path(__file__).resolve().parents[2]
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


def mem_peak_bw(env: dict) -> float | None:
    g = (env.get("gpus") or [{}])[0]
    name, mclk = (g.get("name") or "").lower(), num(g.get("clocks.max.memory"))
    bits = next((b for k, b in BUS_BITS.items() if k in name), None)
    return 2 * mclk * 1e6 * bits / 8 if bits and mclk else None


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


# ---------------------------------------------------------------------------------- the engine
def load_trace(n: int, compress: float, prompt_cap: int, out_cap: int) -> list[dict]:
    """First ``n`` requests of trace_s1.csv, lengths / 8 (capped), inter-arrival times / ``compress``."""
    import csv
    rows = list(csv.DictReader(open(PKG / "starter-kit" / "data" / "trace_s1.csv", encoding="utf-8")))[:n]
    t0 = float(rows[0]["arrival_s"])
    return [{"request_id": r["request_id"], "tenant": r["tenant"], "arrival_s": (float(r["arrival_s"]) - t0) / compress,
             "prompt_tokens": max(16, min(prompt_cap, int(r["prompt_tokens"]) // 8)),
             "output_tokens": max(2, min(out_cap, int(r["output_tokens"]) // 8))} for r in rows]


def serve(ctx, m, trace: list[dict], max_num_seqs: int) -> dict:
    """Replay ``trace`` in real time. FIFO admission while running < max_num_seqs; a newly admitted request's
    whole prompt is prefilled in its own iteration (prefill-priority, no chunking); otherwise one batched
    decode step for all running sequences. Running sequences occupy KV slots 0..n-1 (compacted on finish)."""
    torch = ctx.torch
    gen = torch.Generator().manual_seed(7)
    prompts = {r["request_id"]: torch.randint(0, m.V, (r["prompt_tokens"],), generator=gen).to(ctx.device) for r in trace}
    pending = sorted(trace, key=lambda r: r["arrival_s"])
    running: list[dict] = []
    done: list[dict] = []
    steps: list[dict] = []
    t0 = time.perf_counter()
    now = lambda: time.perf_counter() - t0  # noqa: E731
    with torch.inference_mode():
        while pending or running:
            if pending and pending[0]["arrival_s"] <= now() and len(running) < max_num_seqs:
                r = dict(pending.pop(0))
                slot = len(running)
                ts = now()
                tok = int(m.prefill(prompts[r["request_id"]], slot).item())       # .item() synchronises
                te = now()
                steps.append({"kind": "prefill", "tokens": r["prompt_tokens"], "batch": 1, "dur_s": te - ts})
                r.update(first_token_s=te, token_times=[te], last_token=tok, cached=r["prompt_tokens"], queue_s=ts - r["arrival_s"])
                running.append(r)
            elif running:
                toks = torch.tensor([r["last_token"] for r in running], device=ctx.device)
                lens = torch.tensor([r["cached"] for r in running], device=ctx.device)
                ts = now()
                out = m.decode(toks, lens).tolist()
                te = now()
                steps.append({"kind": "decode", "tokens": len(running), "batch": len(running), "dur_s": te - ts,
                              "ctx_total": int(sum(r["cached"] for r in running))})
                for r, tok in zip(running, out):
                    r["token_times"].append(te)
                    r["last_token"], r["cached"] = tok, r["cached"] + 1
            else:
                time.sleep(max(0.0, min(0.01, pending[0]["arrival_s"] - now())))
            for i in range(len(running) - 1, -1, -1):                            # finish and compact slots
                r = running[i]
                if len(r["token_times"]) >= r["output_tokens"]:
                    last = len(running) - 1
                    if i != last:
                        m.k[:, i] = m.k[:, last]
                        m.v[:, i] = m.v[:, last]
                        running[i] = running[last]
                    running.pop()
                    done.append(r)
    wall = now()
    reqs = []
    for r in sorted(done, key=lambda x: x["arrival_s"]):
        tt = r["token_times"]
        gaps = [b - a for a, b in zip(tt, tt[1:])]
        reqs.append({k: r[k] for k in ("request_id", "tenant", "arrival_s", "prompt_tokens", "output_tokens", "queue_s")} |
                    {"status": "ok", "preemptions": 0, "first_token_s": r["first_token_s"], "finish_s": tt[-1],
                     "ttft_s": r["first_token_s"] - r["arrival_s"], "e2e_s": tt[-1] - r["arrival_s"],
                     "tpot_s": (tt[-1] - tt[0]) / (len(tt) - 1) if len(tt) > 1 else None, "itl": gaps,
                     "tokens_emitted": len(tt)})
    return {"requests": reqs, "steps": steps, "wall_s": wall, "max_num_seqs": max_num_seqs}


def pct(xs, p):
    s = sorted(xs)
    return s[min(len(s) - 1, round(p / 100 * (len(s) - 1)))] if s else float("nan")


def sli(run: dict, slo: dict) -> dict:
    """The L1 SLI summary (serving.summarize) over measured requests; own percentiles as a fallback."""
    reqs = run["requests"]
    ref, src = load_l1("serving")
    out = None
    if ref is not None:
        try:
            import pandas as pd
            df = pd.DataFrame([{k: v for k, v in r.items() if k != "itl"} for r in reqs])
            df.attrs["itl_s"] = __import__("numpy").array([g for r in reqs for g in r["itl"]])
            df.attrs["itl_arrival_s"] = __import__("numpy").array([r["arrival_s"] for r in reqs for _ in r["itl"]])
            s2 = dict(slo, warmup_exclude_s=0, cooldown_exclude_s=0)
            out = {k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v) for k, v in ref.summarize(df, s2).items()}
            out["sli_source"] = src
        except NotImplementedError:
            out = None
    if out is None:
        itl = [g for r in reqs for g in r["itl"]]
        tp = [r["tpot_s"] for r in reqs if r["tpot_s"] is not None]
        out = {"ttft_p50_s": pct([r["ttft_s"] for r in reqs], 50), "ttft_p95_s": pct([r["ttft_s"] for r in reqs], 95),
               "tpot_p50_s": pct(tp, 50), "tpot_p95_s": pct(tp, 95), "itl_p99_s": pct(itl, 99), "sli_source": "experiment fallback"}
    target = slo["ttft_p95_s"] - slo.get("frontend_budget_s", 0)
    good = [r for r in reqs if r["ttft_s"] <= target and (r["tpot_s"] or 0) <= slo["tpot_p95_s"]]
    out["goodput_frac_measured"] = len(good) / len(reqs)
    out["goodput_rps"] = len(good) / run["wall_s"]
    out["output_tok_per_s_wall"] = sum(r["tokens_emitted"] for r in reqs) / run["wall_s"]
    out["itl_p50_s"] = pct([g for r in reqs for g in r["itl"]], 50)
    out["queue_p95_s"] = pct([r["queue_s"] for r in reqs], 95)
    return out


def simulate_l1(trace, m, ceil, overhead_s, max_num_seqs, slo, mem_gb) -> dict:
    """The L1 discrete-event simulator on the identical trace, hardware = this device's measured ceilings."""
    ref, src = load_l1("serving")
    if ref is None:
        return {"available": False, "why": "no L1 serving model found"}
    import pandas as pd
    model = {"params": m.params_nonembed, "layers": m.L, "hidden": m.d, "q_heads": m.H, "kv_heads": m.H, "head_dim": m.hd,
             "kv_dtype_bytes": m.emb.element_size(), "weight_bytes_per_param": {"bf16": m.weight_bytes / m.params_nonembed}}
    hw = {"hbm_bytes_per_gpu": mem_gb * 1e9, "hbm_bw_bytes_per_s": ceil["copy_bytes_per_s"],
          "peak_flops": {"bf16": ceil["gemm_flops"]}, "hbm_bw_efficiency": 1.0, "prefill_mfu": 1.0,
          "runtime_reserve_bytes_per_gpu": 0.5e9, "iteration_overhead_s": {"1": overhead_s}}
    cfg = {"tp": 1, "dtype": "bf16", "max_num_seqs": max_num_seqs, "max_num_batched_tokens": 4096, "chunked_prefill": False,
           "max_model_len": 4096, "gpu_memory_utilization": 0.9, "replicas_per_node": 1}
    df = pd.DataFrame(trace)
    try:
        res = ref.simulate(df, model, hw, cfg)
        s = ref.summarize(res, dict(slo, warmup_exclude_s=0, cooldown_exclude_s=0))
    except NotImplementedError as e:
        return {"available": False, "why": f"starter serving.py not implemented yet ({e})"}
    return {"available": True, "source": src, **{k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
                                                  for k, v in s.items()}}


def stack_probe() -> dict:
    return {"vllm": importlib.util.find_spec("vllm") is not None, "sglang": importlib.util.find_spec("sglang") is not None,
            "hf_cache": Path("~/.cache/huggingface/hub").expanduser().is_dir(),
            "network_interfaces": sorted(os.listdir("/sys/class/net")) if Path("/sys/class/net").is_dir() else [],
            "kubectl": bool(shutil.which("kubectl"))}


def run(ctx) -> dict:
    torch = ctx.torch
    gpu = ctx.is_gpu
    if not gpu:
        torch.set_num_threads(min(8, os.cpu_count() or 1))
    if gpu:
        cfg = dict(d=2048, layers=8, heads=16, vocab=8192, dtype=torch.float16)
        n_req, compress, pcap, ocap = (40, 4.0, 512, 64) if ctx.quick else (160, 4.0, 1024, 128)
        configs = [2, 16]
    else:
        cfg = dict(d=512, layers=4, heads=8, vocab=4096, dtype=torch.float32)
        n_req, compress, pcap, ocap = (32, 8.0, 256, 32) if ctx.quick else (80, 8.0, 512, 64)
        configs = [2, 16]
    trace = load_trace(n_req, compress, pcap, ocap)
    max_len = pcap + ocap + 8
    m = Decoder(torch, device=ctx.device, max_batch=max(configs), max_len=max_len, **cfg)
    ceil = measured_ceilings(ctx)
    # One-point calibration of the per-iteration overhead: a batch-1 decode step minus its pure memory time.
    with torch.inference_mode():
        m.k[:, 0, :, :256].normal_(0, 0.02)
        m.v[:, 0, :, :256].normal_(0, 0.02)
        lens = torch.tensor([256], device=ctx.device)
        tok = torch.tensor([1], device=ctx.device)
        st = ctx.bench(lambda: m.decode(tok, lens), warmup=3, reps=ctx.reps(20))
    mem_t = (m.weight_bytes + 257 * m.kv_bytes_per_token) / ceil["copy_bytes_per_s"]
    overhead = max(0.0, st["median"] - mem_t)
    ctx.log(f"model {m.params_nonembed / 1e6:.0f} M params; trace {len(trace)} requests at "
            f"{len(trace) / trace[-1]['arrival_s']:.1f} req/s; decode B=1 {st['median'] * 1e3:.2f} ms (overhead {overhead * 1e3:.2f} ms)")

    slo_path = PKG / "starter-kit" / "data" / "slo.yaml"
    import yaml
    slo = yaml.safe_load(open(slo_path, encoding="utf-8"))
    mem_gb = (torch.cuda.get_device_properties(0).total_memory / 1e9) if gpu else 8.0
    runs, summary = {}, {}
    for mns in configs:
        serve(ctx, m, trace[: min(6, len(trace))], mns)          # warm-up replay (allocator, kernels, clocks)
        r = serve(ctx, m, trace, mns)
        runs[mns] = r
        s = sli(r, slo)
        s["sim"] = simulate_l1(trace, m, ceil, overhead, mns, slo, mem_gb)
        summary[mns] = s
        ctx.log(f"max_num_seqs={mns:3d}: TTFT p50/p95 {s['ttft_p50_s'] * 1e3:.0f}/{s['ttft_p95_s'] * 1e3:.0f} ms, "
                f"TPOT p50/p95 {s['tpot_p50_s'] * 1e3:.1f}/{s['tpot_p95_s'] * 1e3:.1f} ms, goodput {s['goodput_frac_measured'] * 100:.0f} %, "
                f"{s['output_tok_per_s_wall']:.0f} tok/s")
    small, big = configs
    dec_steps = {mns: [s for s in runs[mns]["steps"] if s["kind"] == "decode"] for mns in configs}
    roof = []
    for st_ in dec_steps[big]:
        byts = m.weight_bytes + st_["ctx_total"] * m.kv_bytes_per_token
        roof.append({"batch": st_["batch"], "dur_s": st_["dur_s"], "mem_floor_s": byts / ceil["copy_bytes_per_s"]})
    by_batch = {}
    for r in roof:
        by_batch.setdefault(r["batch"], []).append(r)
    decode_table = [{"batch": b, "n_steps": len(v), "median_ms": statistics.median(x["dur_s"] for x in v) * 1e3,
                     "p95_ms": pct([x["dur_s"] for x in v], 95) * 1e3,
                     "mem_floor_ms": statistics.median(x["mem_floor_s"] for x in v) * 1e3} for b, v in sorted(by_batch.items())]
    metrics = {f"goodput_frac_mns{k}": round(v["goodput_frac_measured"], 3) for k, v in summary.items()}
    metrics.update({f"ttft_p95_ms_mns{k}": round(v["ttft_p95_s"] * 1e3, 1) for k, v in summary.items()})
    metrics.update({f"tpot_p95_ms_mns{k}": round(v["tpot_p95_s"] * 1e3, 2) for k, v in summary.items()})
    probe = stack_probe()
    return {"metrics": metrics, "summary": {str(k): v for k, v in summary.items()},
            "tables": {"decode_steps_by_batch": decode_table,
                       "requests": {str(k): [{x: y for x, y in r.items() if x != "itl"} for r in v["requests"]] for k, v in runs.items()}},
            "trace": {"n": len(trace), "compress": compress, "prompt_cap": pcap, "output_cap": ocap,
                      "offered_rps": len(trace) / trace[-1]["arrival_s"],
                      "mean_prompt": statistics.fmean(r["prompt_tokens"] for r in trace),
                      "mean_output": statistics.fmean(r["output_tokens"] for r in trace),
                      "output_tokens_requested": sum(r["output_tokens"] for r in trace)},
            "model": {"d": m.d, "layers": m.L, "params_nonembed": m.params_nonembed, "weight_bytes": m.weight_bytes,
                      "kv_bytes_per_token": m.kv_bytes_per_token, "dtype": str(cfg["dtype"])},
            "ceilings": ceil, "overhead_s": overhead, "slo": slo, "configs": configs, "probe": probe,
            "not_runnable_parts": [
                {"part": "supported serving stack (vLLM/SGLang) with an open model, TP=8 on an HX8 node",
                 "probe": f"vllm installed={probe['vllm']}, sglang installed={probe['sglang']}, HF cache={probe['hf_cache']}, "
                          f"network interfaces={probe['network_interfaces']} (container runs with --network none), GPUs="
                          f"{torch.cuda.device_count() if gpu else 0}",
                 "needs": ["serving stack image", "open model weights", "8-GPU node for TP=8"],
                 "fallback": "minimal continuous-batching engine on a random-weight model, same trace shape"},
                {"part": "L3 multi-replica routing, canary and rollback drill",
                 "probe": "single host, no load balancer, no second node", "needs": ["2+ nodes", "load balancer"],
                 "fallback": "two configurations compared under the identical trace on one replica"}],
            "notes": ["Trace: first N requests of data/trace_s1.csv; prompt and output lengths / 8 (capped), inter-arrival "
                      "times / compress. Arrivals replayed in real time (open loop).",
                      "Latencies are engine-side wall clock (perf_counter) including queueing; each step synchronises on "
                      "its sampled tokens, as a real engine must before streaming them.",
                      "A short warm-up replay precedes each measured replay; one measured replay per configuration "
                      "(every request is one sample: percentiles are over requests and token gaps)."]}


def check(result: dict, env: dict) -> list[str]:
    fails = []
    small, big = result["configs"]
    want = result["trace"]["n"]
    for k, reqs in result["tables"]["requests"].items():
        if len(reqs) != want:
            fails.append(f"max_num_seqs={k}: {len(reqs)} of {want} requests completed: the engine dropped requests")
        if any(r["tokens_emitted"] != r["output_tokens"] for r in reqs):
            fails.append(f"max_num_seqs={k}: emitted token counts differ from the requested output lengths")
        if any(r["ttft_s"] <= 0 or r["ttft_s"] > r["e2e_s"] + 1e-9 for r in reqs):
            fails.append(f"max_num_seqs={k}: TTFT must be positive and <= E2E for every request: check the clock bookkeeping")
    s, b = result["summary"][str(small)], result["summary"][str(big)]
    # Same trace, more batch slots: queueing can only shrink, so goodput must not fall and TTFT p95 must not grow much.
    if b["goodput_frac_measured"] + 0.05 < s["goodput_frac_measured"]:
        fails.append(f"goodput fell from {s['goodput_frac_measured']:.2f} to {b['goodput_frac_measured']:.2f} when max_num_seqs grew "
                     f"{small}->{big} on the same trace: check slot compaction (a finished sequence must free its slot)")
    if b["ttft_p95_s"] > 1.25 * s["ttft_p95_s"] + 0.02:
        fails.append("TTFT p95 grew with more batch slots on the same trace: admission is not FIFO or slots leak")
    # Physics: no decode step can beat the memory floor (all weights + KV read once at the measured copy bandwidth).
    for row in result["tables"]["decode_steps_by_batch"]:
        if row["median_ms"] < 0.9 * row["mem_floor_ms"]:
            fails.append(f"decode at batch {row['batch']} took {row['median_ms']:.2f} ms, below the memory floor "
                         f"{row['mem_floor_ms']:.2f} ms: weights cannot be read faster than the memory system; check the byte count")
    if env["device"] == "cuda":
        rows = result["tables"]["decode_steps_by_batch"]
        b1 = next((r for r in rows if r["batch"] == 1), None)
        b4 = next((r for r in rows if r["batch"] == 4), None)
        if b1 and b4 and b4["n_steps"] >= 5 and b1["n_steps"] >= 5 and b4["median_ms"] > 1.7 * b1["median_ms"]:
            fails.append(f"decode step at batch 4 is {b4['median_ms'] / b1['median_ms']:.1f}x batch 1: memory-bound decode should be "
                         "nearly flat in batch; check for per-step weight copies or contention from another GPU job")
        bw = mem_peak_bw(env)
        if bw and result["ceilings"]["copy_bytes_per_s"] > 1.05 * bw:
            fails.append("measured device copy bandwidth exceeds the memory peak: check the copy size (L2-resident?)")
        if b["output_tok_per_s_wall"] <= s["output_tok_per_s_wall"] * 0.95 and s["goodput_frac_measured"] < 0.99:
            fails.append("a larger decode batch did not raise output tokens/s under an overloaded trace: batching is not working")
    return fails


def report(result: dict, env: dict) -> str:
    gpu = env["device"] == "cuda"
    t, md, slo = result["trace"], result["model"], result["slo"]
    L = ["## Workload", "",
         f"Random-weight decoder ({md['params_nonembed'] / 1e6:.0f} M parameters, {md['dtype']}, {md['weight_bytes'] / 1e6:.0f} MB weights). "
         f"Trace: first {t['n']} requests of `trace_s1.csv`, lengths / 8 (prompt cap {t['prompt_cap']}, output cap {t['output_cap']}), "
         f"arrivals compressed {t['compress']:g}x -> **{t['offered_rps']:.1f} req/s offered**, mean prompt {t['mean_prompt']:.0f}, "
         f"mean output {t['mean_output']:.0f} tokens.",
         f"SLO (data/slo.yaml): TTFT p95 <= {slo['ttft_p95_s']} s (engine target {slo['ttft_p95_s'] - slo.get('frontend_budget_s', 0):.2f} s), "
         f"TPOT p95 <= {slo['tpot_p95_s'] * 1e3:.0f} ms, ITL p99 <= {slo.get('itl_p99_s', 0) * 1e3:.0f} ms.",
         "", "## Measured vs simulated, identical trace", "",
         "| max_num_seqs | source | TTFT p50 (ms) | TTFT p95 (ms) | TPOT p50 (ms) | TPOT p95 (ms) | ITL p99 (ms) | goodput | out tok/s |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k in result["configs"]:
        s = result["summary"][str(k)]
        L.append(f"| {k} | measured | {s['ttft_p50_s'] * 1e3:.0f} | {s['ttft_p95_s'] * 1e3:.0f} | {s['tpot_p50_s'] * 1e3:.1f} | "
                 f"{s['tpot_p95_s'] * 1e3:.1f} | {s.get('itl_p99_s', float('nan')) * 1e3:.1f} | {s['goodput_frac_measured'] * 100:.0f} % | "
                 f"{s['output_tok_per_s_wall']:.0f} |")
        sim = s["sim"]
        if sim.get("available"):
            L.append(f"| {k} | L1 simulator | {sim['ttft_p50_s'] * 1e3:.0f} | {sim['ttft_p95_s'] * 1e3:.0f} | {sim['tpot_p50_s'] * 1e3:.1f} | "
                     f"{sim['tpot_p95_s'] * 1e3:.1f} | {sim['itl_p99_s'] * 1e3:.1f} | {sim['goodput_frac'] * 100:.0f} % | "
                     f"{sim['output_tokens_per_s']:.0f} |")
    src = result["summary"][str(result["configs"][0])].get("sli_source")
    L += ["", f"Measured SLIs use the L1 definitions in `{src}` (`summarize`, warm-up/cool-down exclusion set to 0 for this short replay); "
          "goodput = share of requests meeting both the TTFT target and the TPOT SLO. Simulator rows: `serving.simulate` on the same "
          f"trace with this device's measured ceilings (GEMM {result['ceilings']['gemm_flops'] / 1e12:.1f} TFLOP/s, copy "
          f"{result['ceilings']['copy_bytes_per_s'] / 1e9:.0f} GB/s, efficiency 1.0) and a one-point overhead calibration "
          f"({result['overhead_s'] * 1e3:.2f} ms per iteration) `[SIMULATED]`.",
          "", "## Decode iterations (max_num_seqs = %d run)" % result["configs"][1], "",
          "| Batch | steps | median (ms) | p95 (ms) | memory floor (ms) |", "|---|---|---|---|---|"]
    for r in result["tables"]["decode_steps_by_batch"]:
        L.append(f"| {r['batch']} | {r['n_steps']} | {r['median_ms']:.2f} | {r['p95_ms']:.2f} | {r['mem_floor_ms']:.2f} |")
    L += ["", "## Not runnable here", ""]
    for p in result["not_runnable_parts"]:
        L.append(f"- **{p['part']}**. Probe: {p['probe']}. Needs: {', '.join(p['needs'])}. Fallback: {p['fallback']}.")
    s0, s1 = (result["summary"][str(k)] for k in result["configs"])
    L += ["", "## What to conclude", "",
          f"- Same model, same GPU, same trace: raising max_num_seqs {result['configs'][0]} -> {result['configs'][1]} moved goodput "
          f"{s0['goodput_frac_measured'] * 100:.0f} % -> {s1['goodput_frac_measured'] * 100:.0f} % and TTFT p95 "
          f"{s0['ttft_p95_s'] * 1e3:.0f} -> {s1['ttft_p95_s'] * 1e3:.0f} ms. With few slots the queue, not the model, sets TTFT.",
          "- Decode steps barely slow as the batch grows (each step streams the weights once), which is why continuous batching "
          "buys throughput almost for free until KV capacity or the TPOT SLO binds.",
          "- Where measured and simulated rows differ, the usual causes are: the engine prefills one prompt per iteration "
          "(the simulator packs prefill and decode into one budgeted iteration), Python launch overhead that varies with batch, "
          "and other tenants on the GPU. Name the cause before trusting either number."]
    if gpu:
        L.append("- This is a **laptop Ada GPU with a ~0.4 B-parameter random model, not W-INFER 70B on an HX8 node**: only "
                 "the mechanisms transfer, not the milliseconds.")
    else:
        L.append("- _CPU fallback: no GPU was used; a smaller fp32 model served the trace slice. GPU-only invariants (flat "
                 "memory-bound decode, memory-peak bound) were skipped._ On a CPU, decode is closer to compute-bound, so TPOT "
                 "grows visibly with batch: the throughput-vs-latency trade-off the GPU hides at small batch.")
    return "\n".join(L)
