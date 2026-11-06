#!/usr/bin/env python3
"""Chapter 1 hands-on lab: your GPU against its ceilings (measurement half).

Runs on the GPU (hold the GPU lock: run.sh does this) and writes raw outputs into --out:

  gpu_inventory.json        torch device properties, nvidia-smi clocks and limits, field availability
  ch01_telemetry.csv        nvidia-smi samples at ~100 ms for the whole run (power, SM clock, reasons)
  segments.json             wall-clock start/end of every measured segment (to cut the telemetry)
  ceiling_gemm.json         Step 2: large BF16 GEMM, achieved FLOP/s (empirical compute ceiling)
  ceiling_copy.json         Step 2: device-to-device copy, achieved bytes/s (empirical memory ceiling)
  gemv_sweep.csv            Step 3: Y = X @ W with batch B from 1 to 4096 (decode-like to GEMM-like)
  train_steps.csv           Step 4: every timed training step, per batch size
  train_model.json          Step 4: model shape, parameter count, FLOPs per token, saved-activation bytes

Analysis (ceiling model, MFU, classification) is in ch01_analyze.py, so it can be re-run on the raw data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

from ch01_telemetry import Telemetry, save_json

DEV = "cuda"


# ---------------------------------------------------------------------------------------------- model
class Block(nn.Module):
    def __init__(self, d: int, h: int):
        super().__init__()
        self.h = h
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.proj = nn.Linear(d, 3 * d), nn.Linear(d, d)
        self.fc1, self.fc2 = nn.Linear(d, 4 * d), nn.Linear(4 * d, d)

    def forward(self, x):
        b, s, d = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(d, dim=-1)
        q, k, v = (t.view(b, s, self.h, d // self.h).transpose(1, 2) for t in (q, k, v))
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.proj(a.transpose(1, 2).reshape(b, s, d))
        return x + self.fc2(F.gelu(self.fc1(self.ln2(x))))


class TinyGPT(nn.Module):
    """A small decoder-only transformer (GPT-2-small-like widths, 8 layers), weights tied to the head."""

    def __init__(self, vocab: int, d: int, layers: int, heads: int, seq: int):
        super().__init__()
        self.tok, self.pos = nn.Embedding(vocab, d), nn.Embedding(seq, d)
        self.blocks = nn.ModuleList(Block(d, heads) for _ in range(layers))
        self.ln = nn.LayerNorm(d)

    def forward(self, idx):
        x = self.tok(idx) + self.pos(torch.arange(idx.shape[1], device=idx.device))
        for blk in self.blocks:
            x = blk(x)
        return self.ln(x) @ self.tok.weight.t()


# ------------------------------------------------------------------------------------------- helpers
def smi(*args: str) -> str:
    return subprocess.run(["nvidia-smi", *args], capture_output=True, text=True, timeout=60).stdout


def timed_loop(fn, seconds: float, inner: int) -> tuple[int, float, float, float]:
    """Run fn in batches of `inner` until `seconds` pass; return (iterations, elapsed_s, t0, t1)."""
    torch.cuda.synchronize()
    t0 = time.time()
    p0 = time.perf_counter()
    n = 0
    while time.perf_counter() - p0 < seconds:
        for _ in range(inner):
            fn()
        torch.cuda.synchronize()
        n += inner
    el = time.perf_counter() - p0
    return n, el, t0, t0 + el


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--quick", action="store_true", help="shorter windows (smoke test, not for evidence)")
    a = ap.parse_args()
    out: Path = a.out
    out.mkdir(parents=True, exist_ok=True)
    sec = 2.0 if a.quick else 6.0
    torch.manual_seed(0)
    torch.backends.cuda.matmul.allow_tf32 = False

    # Step 1 -- inventory -----------------------------------------------------------------------------
    p = torch.cuda.get_device_properties(0)
    tel = Telemetry(out / "ch01_telemetry.csv")
    inv = {
        "name": p.name, "compute_capability": f"{p.major}.{p.minor}", "sm_count": p.multi_processor_count,
        "total_memory_bytes": p.total_memory, "l2_cache_bytes": getattr(p, "L2_cache_size", None),
        "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
        "nvidia_smi_fields": tel.availability,
    }
    save_json(inv, out / "gpu_inventory.json")
    (out / "nvidia_smi_q_before.txt").write_text(smi("-q", "-d", "CLOCK,POWER,PERFORMANCE,TEMPERATURE"))
    segments: dict[str, list[float]] = {}

    tel.start()
    try:
        # idle reference
        t0 = time.time(); time.sleep(3.0 if not a.quick else 1.0); segments["idle"] = [t0, time.time()]

        # Step 2 -- empirical ceilings -------------------------------------------------------------------
        n = 8192
        A = torch.randn(n, n, device=DEV, dtype=torch.bfloat16)
        B = torch.randn(n, n, device=DEV, dtype=torch.bfloat16)
        for _ in range(3):
            A @ B
        it, el, t0, t1 = timed_loop(lambda: A @ B, sec, 4)
        segments["gemm"] = [t0, t1]
        save_json({"m": n, "n": n, "k": n, "dtype": "bfloat16", "iterations": it, "elapsed_s": el,
                   "flop_per_iter": 2 * n ** 3, "achieved_flops": 2 * n ** 3 * it / el}, out / "ceiling_gemm.json")
        del A, B

        x = torch.empty(256 * 2 ** 20, dtype=torch.float32, device=DEV)   # 1 GiB
        y = torch.empty_like(x)
        y.copy_(x)
        it, el, t0, t1 = timed_loop(lambda: y.copy_(x), sec, 8)
        segments["copy"] = [t0, t1]
        nbytes = 2 * x.numel() * 4  # read + write
        save_json({"buffer_bytes": x.numel() * 4, "bytes_moved_per_iter": nbytes, "iterations": it,
                   "elapsed_s": el, "achieved_bytes_per_s": nbytes * it / el}, out / "ceiling_copy.json")
        del x, y
        torch.cuda.empty_cache()

        # Step 3 -- decode-like to GEMM-like: Y[B, d] = X[B, d] @ W[d, d] ----------------------------------
        d = 8192
        W = torch.randn(d, d, device=DEV, dtype=torch.bfloat16)              # 128 MiB: 4x the L2 cache
        rows = []
        for bsz in (1, 4, 16, 64, 256, 1024, 4096):
            X = torch.randn(bsz, d, device=DEV, dtype=torch.bfloat16)
            for _ in range(5):
                X @ W
            inner = max(1, 2048 // bsz)
            it, el, t0, t1 = timed_loop(lambda: X @ W, 1.0 if not a.quick else 0.4, inner)
            segments[f"gemv_B{bsz}"] = [t0, t1]
            rows.append({"batch": bsz, "d": d, "iterations": it, "elapsed_s": el,
                         "flop_per_iter": 2 * bsz * d * d,
                         "bytes_per_iter_min": 2 * d * d + 2 * 2 * bsz * d})  # W once, X read, Y written
        with open(out / "gemv_sweep.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        del W, X
        torch.cuda.empty_cache()

        # Step 4 -- a real training step at three batch sizes ----------------------------------------------
        cfg = dict(vocab=8192, d=768, layers=8, heads=12, seq=512)
        model = TinyGPT(**cfg).to(DEV)
        opt = torch.optim.AdamW(model.parameters(), lr=3e-4, fused=True)
        n_total = sum(q.numel() for q in model.parameters())
        n_flop = n_total - model.pos.weight.numel()   # position table does no matmul work
        attn_flop_tok = 12 * cfg["layers"] * cfg["d"] * cfg["seq"]   # PaLM convention, fwd + bwd

        def step(idx, tgt):
            with torch.autocast("cuda", dtype=torch.bfloat16):
                logits = model(idx)
                loss = F.cross_entropy(logits.float().view(-1, cfg["vocab"]), tgt.view(-1))
            loss.backward()
            opt.step()
            opt.zero_grad(set_to_none=True)
            return loss

        # bytes saved for backward in one forward pass at the largest batch (unique storages)
        def saved_bytes(bsz: int) -> int:
            seen: dict[int, int] = {}

            def pack(t):
                try:
                    s = t.untyped_storage()
                    seen[s.data_ptr()] = s.nbytes()
                except Exception:  # noqa: BLE001
                    pass
                return t

            idx = torch.randint(0, cfg["vocab"], (bsz, cfg["seq"]), device=DEV)
            with torch.autograd.graph.saved_tensors_hooks(pack, lambda t: t):
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    logits = model(idx)
                    loss = F.cross_entropy(logits.float().view(-1, cfg["vocab"]), idx.view(-1))
            param_ptrs = {q.untyped_storage().data_ptr() for q in model.parameters()}
            act = sum(v for k, v in seen.items() if k not in param_ptrs)
            del logits, loss
            return act

        batches = (1, 4, 16)
        saved = {b: saved_bytes(b) for b in batches}
        torch.cuda.empty_cache()
        step_rows = []
        losses = {}
        for bsz in batches:
            idx = torch.randint(0, cfg["vocab"], (bsz, cfg["seq"]), device=DEV)
            tgt = torch.roll(idx, -1, dims=1)
            for _ in range(5):
                step(idx, tgt)            # warm-up: allocator, kernels, optimizer state
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
            t0 = time.time()
            p0 = time.perf_counter()
            k = 0
            while (time.perf_counter() - p0 < sec) or k < 10:
                s0 = time.perf_counter()
                loss = step(idx, tgt)
                torch.cuda.synchronize()
                step_rows.append({"batch": bsz, "seq": cfg["seq"], "step": k,
                                  "step_s": time.perf_counter() - s0, "t_end": time.time()})
                k += 1
            segments[f"train_B{bsz}"] = [t0, time.time()]
            losses[bsz] = float(loss)
            step_rows[-1]["peak_mem_bytes"] = torch.cuda.max_memory_allocated()
        with open(out / "train_steps.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["batch", "seq", "step", "step_s", "t_end", "peak_mem_bytes"])
            w.writeheader(); w.writerows(step_rows)
        save_json({"config": cfg, "params_total": n_total, "params_for_flops": n_flop,
                   "flop_per_token_6N": 6 * n_flop, "flop_per_token_attention": attn_flop_tok,
                   "saved_activation_bytes": {str(b): v for b, v in saved.items()},
                   "final_loss": {str(b): v for b, v in losses.items()},
                   "optimizer": "AdamW fused, fp32 master weights, bf16 autocast",
                   "loss_is_finite": all(math.isfinite(v) for v in losses.values())},
                  out / "train_model.json")

        t0 = time.time(); time.sleep(2.0 if not a.quick else 0.5); segments["idle_after"] = [t0, time.time()]
    finally:
        tel.stop()
        save_json(segments, out / "segments.json")
    (out / "nvidia_smi_q_after.txt").write_text(smi("-q", "-d", "CLOCK,POWER,PERFORMANCE,TEMPERATURE"))
    print(f"raw outputs written to {out}")


if __name__ == "__main__":
    main()
