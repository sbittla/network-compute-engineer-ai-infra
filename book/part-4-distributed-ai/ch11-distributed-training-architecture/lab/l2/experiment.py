"""Ch 11 L2: step time and peak memory of a scaled-down W-TRAIN-shaped model on one GPU, vs the L1 model.

What it teaches (Section 11.2 memory accounting, Section 11.10 step-time model): the lab's
``memory_per_gpu`` and ``step_time`` formulas are planning estimates. Here a small GPT-style stack
(pre-LN attention + 4h GELU MLP, BF16 autocast, FP32 Adam) is trained for real, and four things are
measured and compared with the L1 model:

1. **Model state** bytes per parameter (allocator delta after the first Adam step) vs the 16 B/param
   convention of Section 11.2.
2. **Activation memory per layer**, measured two ways: the bytes the autograd graph saves for
   backward (``saved_tensors_hooks``, works on any device) and, on the GPU, the peak-allocated slope
   versus layer count. Both are expressed as the coefficient ``c`` in ``A_layer = c * s*b*h`` and
   compared with Korthikanti et al.'s 34 (fused/flash attention) and ``34 + 5as/h`` (attention scores
   materialized). Full recomputation should collapse ``c`` to the stored layer input (~2-4).
3. **Step time** vs the L1 ``compute_s = 6*N*T*rf / (peak * kernel_efficiency)`` with world size 1,
   which backs out the real kernel efficiency of this stack (the lab assumes 0.5).
4. **Recompute cost**: measured step-time ratio full/no recompute vs the model's 1.333.

CPU fallback: the same model at a smaller size trains on the CPU (FP32, no autocast). Activation bytes
come from the saved-tensor hooks (an exact count of what autograd keeps, independent of the
allocator), and step time is compared with the same L1 formula using a nominal CPU peak; allocator
peak-memory and GPU-peak invariants are skipped.
"""
from __future__ import annotations

import math

EXPERIMENT = {
    "id": "ch11-l2",
    "title": "Lab 11 L2: scaled-down training step - measured memory and step time vs the L1 model",
    "evidence": "MEASURED",
    "cpu_fallback": ("the same GPT-style model, smaller and in FP32, trains on the CPU; activation memory is "
                     "counted exactly with autograd saved-tensor hooks and step time is timed with perf_counter; "
                     "allocator peak-memory and GPU-peak invariants are skipped"),
}

# Dense BF16 tensor-core rate with FP32 accumulate, per SM per clock, Ada (GeForce): NVIDIA Ada Lovelace
# architecture whitepaper, RTX 4090 = 165.2 TFLOP/s dense at 128 SMs x 2520 MHz -> 512 FLOP/clk/SM.
ADA_BF16_FLOP_PER_CLK_SM = 512
L1_KERNEL_EFFICIENCY = 0.5     # data/cluster_orion.yaml kernel_efficiency (ILLUSTRATIVE)
L1_FULL_RECOMPUTE_FACTOR = 1.333
L1_BYTES_PER_PARAM_STATE = 16
KORTHIKANTI_C = 34


def gpu_peak_flops(env: dict) -> tuple[float | None, str]:
    g = (env.get("gpus") or [{}])[0]
    sm = env.get("gpu0", {}).get("sm_count")
    try:
        clk = float(g["clocks.max.sm"]) * 1e6
    except (KeyError, ValueError):
        return None, "unknown"
    name = env.get("gpu0", {}).get("name", "")
    cap = env.get("gpu0", {}).get("capability", "")
    if sm and cap == "8.9":
        return ADA_BF16_FLOP_PER_CLK_SM * sm * clk, (f"Ada whitepaper rate 512 BF16 FLOP/clk/SM x {sm} SMs x "
                                                     f"{clk / 1e6:.0f} MHz max SM clock ({name})")
    return None, f"no peak table entry for {name} (capability {cap})"


def build_model(torch, layers: int, h: int, heads: int, device: str, recompute: bool, attn: str):
    nn, F = torch.nn, torch.nn.functional
    from torch.utils.checkpoint import checkpoint

    class Block(nn.Module):
        def __init__(self):
            super().__init__()
            self.ln1, self.ln2 = nn.LayerNorm(h), nn.LayerNorm(h)
            self.qkv, self.proj = nn.Linear(h, 3 * h), nn.Linear(h, h)
            self.fc1, self.fc2 = nn.Linear(h, 4 * h), nn.Linear(4 * h, h)

        def attn(self, x):
            s, b, _ = x.shape
            q, k, v = self.qkv(self.ln1(x)).view(s, b, 3, heads, h // heads).permute(2, 1, 3, 0, 4)
            if attn == "math":
                with torch.nn.attention.sdpa_kernel(torch.nn.attention.SDPBackend.MATH):
                    o = F.scaled_dot_product_attention(q, k, v, is_causal=True)
            else:
                o = F.scaled_dot_product_attention(q, k, v, is_causal=True)
            return self.proj(o.permute(2, 0, 1, 3).reshape(s, b, h))

        def body(self, x):
            x = x + self.attn(x)
            return x + self.fc2(F.gelu(self.fc1(self.ln2(x))))

        def forward(self, x):
            return checkpoint(self.body, x, use_reentrant=False) if recompute else self.body(x)

    class Stack(nn.Module):
        def __init__(self):
            super().__init__()
            self.blocks = nn.ModuleList(Block() for _ in range(layers))
            self.ln_f = nn.LayerNorm(h)

        def forward(self, x):
            for blk in self.blocks:
                x = blk(x)
            return self.ln_f(x).float().pow(2).mean()

    return Stack().to(device)


def train_case(ctx, *, layers: int, h: int, heads: int, s: int, b: int, recompute: bool, attn: str,
               warmup: int, steps: int) -> dict:
    torch = ctx.torch
    dev = ctx.device
    torch.manual_seed(0)
    model = build_model(torch, layers, h, heads, dev, recompute, attn)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.Adam(model.parameters(), lr=1e-4, fused=ctx.is_gpu)
    x = torch.randn(s, b, h, device=dev)
    amp = torch.autocast("cuda", dtype=torch.bfloat16) if ctx.is_gpu else torch.autocast("cpu", enabled=False)

    def step():
        with amp:
            loss = model(x)
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)
        return loss

    # Saved-activation bytes: what autograd keeps for backward (unique storages, weights excluded).
    param_ptrs = {p.data_ptr() for p in model.parameters()}
    seen: dict[int, int] = {}

    def is_weight_cast(t) -> bool:
        # autocast's BF16 copy of a parameter (often seen through a transpose/view): walk view ops back
        # to ToCopyBackward and test whether its input is a leaf parameter (AccumulateGrad)
        fn = t.grad_fn
        for _ in range(4):
            if fn is None:
                return False
            name = type(fn).__name__
            if name.startswith("ToCopyBackward"):
                return any(type(nf).__name__ == "AccumulateGrad" for nf, _ in fn.next_functions if nf is not None)
            if not name.startswith(("TBackward", "ViewBackward", "TransposeBackward", "PermuteBackward",
                                    "ExpandBackward", "UnsafeViewBackward")):
                return False
            fn = fn.next_functions[0][0] if fn.next_functions else None
        return False

    cast_bytes: dict[int, int] = {}

    def pack(t):
        try:
            st = t.untyped_storage()
            if is_weight_cast(t):
                cast_bytes[st.data_ptr()] = st.nbytes()
                return t
            ptr = st.data_ptr()
            if ptr not in param_ptrs:
                seen[ptr] = max(seen.get(ptr, 0), st.nbytes())
        except (RuntimeError, NotImplementedError):
            pass
        return t

    with torch.autograd.graph.saved_tensors_hooks(pack, lambda t: t):
        with amp:
            loss = model(x)
    saved_bytes = sum(seen.values())
    weight_cast_bytes = sum(cast_bytes.values())
    loss.backward()
    opt.step()                                   # materializes Adam m and v
    del loss
    if ctx.is_gpu:                               # state = weights + grads + m + v, measured with grads alive
        with amp:
            loss = model(x)
        loss.backward()
        del loss
        torch.cuda.synchronize()
        state_bytes = torch.cuda.memory_allocated() - x.numel() * x.element_size()
        opt.step()
    opt.zero_grad(set_to_none=True)
    ctx.sync()

    out = {"layers": layers, "h": h, "heads": heads, "s": s, "b": b, "recompute": recompute, "attn": attn,
           "n_params": n_params, "saved_act_bytes": saved_bytes,
           "autocast_weight_copy_bytes": weight_cast_bytes}
    if ctx.is_gpu:
        torch.cuda.reset_peak_memory_stats()
        base = torch.cuda.memory_allocated()
    st = ctx.bench(step, warmup=warmup, reps=steps)
    if ctx.is_gpu:
        out.update(state_bytes=state_bytes, state_bytes_per_param=state_bytes / n_params,
                   peak_alloc_bytes=torch.cuda.max_memory_allocated(),
                   peak_reserved_bytes=torch.cuda.max_memory_reserved(),
                   peak_over_state_bytes=torch.cuda.max_memory_allocated() - base)
    tokens = s * b
    rf = L1_FULL_RECOMPUTE_FACTOR if recompute else 1.0
    out.update(step_p50_s=st["median"], step_p95_s=st["p95"], step_min_s=st["min"], step_max_s=st["max"],
               step_iqr_s=st["iqr"], measured_steps=st["n"], warmup_steps=warmup,
               useful_flops=6.0 * n_params * tokens,
               # causal attention core: QK^T and AV, fwd 2*2*s^2*h*b/2, x3 for fwd+bwd (x4 with recompute)
               attn_flops=3 * 2 * s * s * h * b * layers * (4 / 3 if recompute else 1.0),
               rf=rf)
    out["act_coeff_saved"] = saved_bytes / layers / (s * b * h)
    del model, opt, x
    if ctx.is_gpu:
        torch.cuda.empty_cache()
    return out


def run(ctx) -> dict:
    torch = ctx.torch
    if ctx.is_gpu:
        h, heads = 1024, 8
        s = 1024 if ctx.quick else 2048
        layer_counts = [2, 4] if ctx.quick else [2, 4, 6]
        warmup, steps = (3, 5) if ctx.quick else (20, 20)
    else:
        torch.set_num_threads(max(1, min(8, torch.get_num_threads())))
        h, heads = 256, 4
        s = 256 if ctx.quick else 512
        layer_counts = [2, 4]
        warmup, steps = (3, 5) if ctx.quick else (5, 10)
    b = 1
    cases = []
    for L in layer_counts:
        cases.append(train_case(ctx, layers=L, h=h, heads=heads, s=s, b=b, recompute=False, attn="flash",
                                warmup=warmup, steps=steps))
    Lmax = layer_counts[-1]
    cases.append(train_case(ctx, layers=Lmax, h=h, heads=heads, s=s, b=b, recompute=True, attn="flash",
                            warmup=warmup, steps=steps))
    cases.append(train_case(ctx, layers=Lmax, h=h, heads=heads, s=s, b=b, recompute=False, attn="math",
                            warmup=warmup, steps=steps))
    for c in cases:
        mem = f" peak {c['peak_alloc_bytes'] / 2**20:.0f} MiB" if "peak_alloc_bytes" in c else ""
        ctx.log(f"L={c['layers']} recompute={c['recompute']!s:5} attn={c['attn']:5} params={c['n_params'] / 1e6:.1f}M "
                f"step p50 {c['step_p50_s'] * 1e3:.2f} ms  saved-act c={c['act_coeff_saved']:.1f}{mem}")

    base = [c for c in cases if not c["recompute"] and c["attn"] == "flash"]
    sbh = s * b * h
    metrics = {"h": h, "s": s, "b": b, "heads": heads, "layer_counts": layer_counts,
               "act_coeff_saved_flash": base[-1]["act_coeff_saved"],
               "act_coeff_saved_full_recompute": cases[-2]["act_coeff_saved"],
               "act_coeff_saved_math_attn": cases[-1]["act_coeff_saved"],
               "korthikanti_score_term_5as_over_h": 5 * heads * s / h,
               "step_p50_s_largest": base[-1]["step_p50_s"],
               "recompute_step_ratio": cases[-2]["step_p50_s"] / base[-1]["step_p50_s"],
               "recompute_act_ratio": cases[-2]["saved_act_bytes"] / base[-1]["saved_act_bytes"]}
    # per-layer slope of step time (removes the fixed final-LN/optimizer-launch cost)
    if len(base) >= 2:
        dl = base[-1]["layers"] - base[0]["layers"]
        metrics["step_s_per_layer"] = (base[-1]["step_p50_s"] - base[0]["step_p50_s"]) / dl
        metrics["params_per_layer"] = (base[-1]["n_params"] - base[0]["n_params"]) / dl
    if ctx.is_gpu:
        dl = base[-1]["layers"] - base[0]["layers"]
        metrics["act_coeff_peak_slope_flash"] = (base[-1]["peak_over_state_bytes"]
                                                 - base[0]["peak_over_state_bytes"]) / dl / sbh
        # what the allocator peak should contain per layer: saved activations + autocast's BF16 weight copies
        metrics["weight_copy_coeff"] = (base[-1]["autocast_weight_copy_bytes"]
                                        - base[0]["autocast_weight_copy_bytes"]) / dl / sbh
        metrics["expected_peak_slope"] = metrics["act_coeff_saved_flash"] + metrics["weight_copy_coeff"]
        metrics["state_bytes_per_param"] = base[-1]["state_bytes_per_param"]
        metrics["peak_memory_allocated_gb"] = base[-1]["peak_alloc_bytes"] / 1e9
        metrics["peak_memory_reserved_gb"] = base[-1]["peak_reserved_bytes"] / 1e9
        metrics["nccl_version"] = ".".join(map(str, torch.cuda.nccl.version()))
    notes = [
        "Model: pre-LN GPT block (fused QKV, causal SDPA, 4h GELU MLP), no embedding/vocab head; input is a random "
        "(s, b, h) tensor and the loss is mean(LN(x)^2). Parameters counted exactly from the module.",
        f"Benchmark: {warmup} warm-up steps then {steps} timed steps per case (CUDA events on the GPU, perf_counter on "
        "the CPU); median, p95, IQR reported.",
        "GPU numeric precision: BF16 autocast with FP32 master weights and FP32 Adam (4+4+4+4 = 16 B/param, the "
        "Section 11.2 convention). PyTorch AMP keeps the residual stream and LayerNorm inputs in FP32, which "
        "Megatron's 34 coefficient (all-BF16 activations) does not; expect c a few units above 34.",
        "Activation coefficient c = saved bytes / (layers x s x b x h); saved bytes are unique storages handed to "
        "autograd's pack hook, excluding parameters and autocast's BF16 weight copies (counted separately: they "
        "live until backward and show up in the allocator peak).",
        "Not runnable here: TP=8 with sequence parallelism and the 1F1B pipeline (needs an 8-GPU node with NVLink, "
        "README Section 8); the s*b*h*34/t division by t therefore is not measured, only the t=1 coefficient.",
    ]
    if not ctx.is_gpu:
        notes.append("CPU fallback: FP32 activations (4 B), so the coefficient is expected near 2 x the BF16 value; "
                     "allocator peak memory is not available on the CPU and is not reported.")
    return {"metrics": metrics, "tables": {"cases": cases}, "notes": notes}


def _expected_coeffs(device: str) -> dict:
    # bytes per activation element: 2 on the GPU (BF16 autocast), 4 on the CPU (FP32)
    scale = 1.0 if device == "cuda" else 2.0
    return {"flash": KORTHIKANTI_C * scale, "scale": scale}


def check(result: dict, env: dict) -> list[str]:
    m = result["metrics"]
    cases = result["tables"]["cases"]
    fails = []
    exp = _expected_coeffs(env["device"])
    c_flash = m["act_coeff_saved_flash"]
    if not 0.8 * exp["flash"] <= c_flash <= 1.35 * exp["flash"]:
        fails.append(f"saved-activation coefficient {c_flash:.1f} is outside [0.8, 1.35] x the Korthikanti "
                     f"{exp['flash']:.0f}: check that SDPA is fused (no s^2 scores saved) and the dtype")
    c_full = m["act_coeff_saved_full_recompute"]
    if not c_full <= 0.25 * c_flash:
        fails.append(f"full recompute kept c={c_full:.1f} (> 25 % of {c_flash:.1f}): checkpoint() is not dropping "
                     "the layer internals; check use_reentrant=False and that every block is wrapped")
    extra = m["act_coeff_saved_math_attn"] - c_flash
    term = m["korthikanti_score_term_5as_over_h"] * exp["scale"]
    if not 0.3 * term <= extra <= 2.0 * term:
        fails.append(f"materialized attention added c={extra:.1f}, expected ~{term:.0f} (5as/h, +-dtype/dropout): "
                     "check that the math SDPA backend really ran")
    base = [c for c in cases if not c["recompute"] and c["attn"] == "flash"]
    if not all(b2["step_p50_s"] > b1["step_p50_s"] for b1, b2 in zip(base, base[1:])):
        fails.append("step time did not grow with layer count: the run is launch/overhead-bound or another "
                     "job is sharing the device; rerun on an idle device")
    if m["recompute_step_ratio"] < 1.05:
        fails.append(f"full recompute step ratio {m['recompute_step_ratio']:.2f} < 1.05: the forward is not being "
                     "recomputed; check torch.utils.checkpoint wrapping")
    if env["device"] == "cuda":
        peak, _ = gpu_peak_flops(env)
        for c in cases:
            achieved = (c["useful_flops"] * c["rf"] + c["attn_flops"]) / c["step_p50_s"]
            if peak and achieved > 1.05 * peak:
                fails.append(f"L={c['layers']} {c['attn']} achieved {achieved / 1e12:.1f} TFLOP/s > device peak "
                             f"{peak / 1e12:.1f}: check the FLOP count or the clock source")
        if not 15.0 <= m["state_bytes_per_param"] <= 19.0:
            fails.append(f"model state {m['state_bytes_per_param']:.1f} B/param, expected ~16 (FP32 w, g, m, v): "
                         "check the optimizer and that gradients were freed (zero_grad(set_to_none=True))")
        slope, want = m["act_coeff_peak_slope_flash"], m["expected_peak_slope"]
        if not 0.75 * want <= slope <= 1.25 * want:
            fails.append(f"allocator peak slope c={slope:.1f} disagrees with saved activations + autocast weight "
                         f"copies ({want:.1f}) by > 25 %: inspect torch.cuda.memory_summary() for transient buffers")
        if result["tables"]["cases"][-1]["peak_alloc_bytes"] > 5e9:
            fails.append("experiment used > 5 GB of VRAM; reduce s or h")
    return fails


def report(result: dict, env: dict) -> str:
    m = result["metrics"]
    gpu = env["device"] == "cuda"
    peak, peak_src = gpu_peak_flops(env) if gpu else (None, "")
    exp = _expected_coeffs(env["device"])
    lines = ["## Cases (median of timed steps)", "",
             "| Layers | Recompute | Attention | Params (M) | Step p50 (ms) | p95 (ms) | IQR (ms) | Saved act c | "
             + ("Peak alloc (MiB) | Achieved TFLOP/s | Kernel eff. |" if gpu else "Achieved GFLOP/s |"),
             "|---|---|---|---|---|---|---|---|" + ("---|---|---|" if gpu else "---|")]
    for c in result["tables"]["cases"]:
        achieved = (c["useful_flops"] * c["rf"] + c["attn_flops"]) / c["step_p50_s"]
        row = (f"| {c['layers']} | {'full' if c['recompute'] else 'none'} | {c['attn']} | {c['n_params'] / 1e6:.1f} | "
               f"{c['step_p50_s'] * 1e3:.2f} | {c['step_p95_s'] * 1e3:.2f} | {c['step_iqr_s'] * 1e3:.2f} | "
               f"{c['act_coeff_saved']:.1f} |")
        if gpu:
            eff = f"{achieved / peak:.2f}" if peak else "n/a"
            row += f" {c['peak_alloc_bytes'] / 2**20:.0f} | {achieved / 1e12:.1f} | {eff} |"
        else:
            row += f" {achieved / 1e9:.1f} |"
        lines.append(row)
    lines += ["", "## Measured vs the L1 model (Section 11.2, `stepmodel.memory_per_gpu` / `step_time`)", "",
              "| Quantity | Measured | L1 model | Note |", "|---|---|---|---|"]
    lines.append(f"| Activation coefficient c (fused attention) | {m['act_coeff_saved_flash']:.1f} | "
                 f"{exp['flash']:.0f} | s*b*h*c bytes per layer{'' if gpu else '; FP32 so 2 x 34'} |")
    if gpu:
        lines.append(f"| c from allocator peak slope | {m['act_coeff_peak_slope_flash']:.1f} | "
                     f"{m['expected_peak_slope']:.1f} | saved activations + autocast BF16 weight copies "
                     f"({m['weight_copy_coeff']:.1f}), which the L1 model does not count |")
    lines.append(f"| c, full recompute | {m['act_coeff_saved_full_recompute']:.1f} | {2 * exp['scale']:.0f} | "
                 "layer input only (FP32 residual under AMP) |")
    lines.append(f"| c, attention scores materialized | {m['act_coeff_saved_math_attn']:.1f} | "
                 f"{exp['flash'] + m['korthikanti_score_term_5as_over_h'] * exp['scale']:.0f} | 34 + 5as/h |")
    lines.append(f"| Recompute step-time ratio | {m['recompute_step_ratio']:.2f} | {L1_FULL_RECOMPUTE_FACTOR} | 8ND vs 6ND |")
    if gpu:
        lines.append(f"| Model state | {m['state_bytes_per_param']:.2f} B/param | {L1_BYTES_PER_PARAM_STATE} B/param | "
                     "FP32 w + g + Adam m, v |")
    if gpu and peak and "step_s_per_layer" in m:
        per_layer_flops = 6 * m["params_per_layer"] * m["s"] * m["b"] + 3 * 2 * m["s"] ** 2 * m["h"] * m["b"]
        eff = per_layer_flops / m["step_s_per_layer"] / peak
        modeled = 6 * m["params_per_layer"] * m["s"] * m["b"] / (peak * L1_KERNEL_EFFICIENCY)
        lines.append(f"| Step time per layer | {m['step_s_per_layer'] * 1e3:.2f} ms | {modeled * 1e3:.2f} ms | "
                     f"compute_s at kernel_efficiency {L1_KERNEL_EFFICIENCY}; measured implies {eff:.2f} |")
        lines += ["", f"Device peak used for efficiency: **{peak / 1e12:.1f} TFLOP/s** dense BF16 `[VENDOR-SPEC]` "
                  f"({peak_src})."]
    lines += ["", "## What to conclude", "",
              "- The s*b*h*34 activation estimate holds to within the AMP dtype difference once attention is fused; "
              "materializing the scores adds the 5as/h term, which at long s dominates (Section 11.2).",
              "- Full recomputation trades about a third more step time for an order of magnitude less activation "
              "memory: the measured ratio is the real price on this stack, not the model's 1.333.",
              "- The kernel efficiency backed out here replaces the ILLUSTRATIVE 0.5 only for this GPU and model "
              "size; small h runs at lower efficiency than a 70B layer would."]
    if gpu:
        lines += ["", "_This is a laptop Ada GPU (RTX 4060 class, 8 GB GDDR6), not an H100 (989 dense BF16 TFLOP/s, "
                  "80 GB HBM3). The peak above uses the maximum SM clock nvidia-smi reports; the sustained laptop "
                  "boost clock is lower, so the efficiencies are conservative. Compare coefficients and ratios with the L1 model, not absolute times._"]
    else:
        lines += ["", "_CPU fallback: no GPU was used. Activation bytes are exact autograd counts; step times are CPU "
                  "times and say nothing about GPU efficiency. GPU-only invariants (device peak, allocator slope, "
                  "16 B/param state) were skipped._"]
    return "\n".join(lines)
