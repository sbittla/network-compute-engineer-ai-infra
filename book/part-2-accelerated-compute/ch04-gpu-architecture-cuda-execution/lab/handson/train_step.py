#!/usr/bin/env python3
"""Ch 4 hands-on: a small language-model training step with a hidden host sync.

Variants (choose with --variant):
  baseline  the loss keeps only real tokens with boolean indexing, per_token_loss[mask].mean(), and a NaN
            guard runs `if not torch.isfinite(loss)` on every micro-batch. Both lines look harmless and both
            make the CPU wait for the GPU (Section 4.6, "Explicit and implicit synchronization", Table 4.3).
  fixed     the loss uses torch.where (static shapes, NaN-safe at padding, as in the chapter's troubleshooting
            fix) and the NaN guard is checked once per step on a GPU-side flag after the step.
  graphed   the fixed step captured once as a CUDA Graph (forward, backward and AdamW for all micro-batches)
            and replayed: one launch per step instead of hundreds (Section 4.5, "Reducing launch overhead"; Table 4.13).

Modes (choose with --mode):
  time        uninstrumented timing: warm-up steps, then timed steps, each closed by a synchronize so the
              window covers the GPU work (the Section 4.10 pitfall). Prints one JSON line.
  profile     torch.profiler over a few steps: CUDA runtime calls per step, and the trace (chrome JSON).
  nsys        NVTX ranges and torch.cuda.profiler.start()/stop() around --capture-steps steps; run it under
              `nsys profile --capture-range=cudaProfilerApi`.
  syncdebug   one step with torch.cuda.set_sync_debug_mode("warn"): every synchronizing call prints a
              warning with the line that made it.
  capture     try to capture the *baseline* step as a CUDA Graph (it must fail: a host sync breaks capture).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import warnings

import torch
import torch.nn.functional as F


def parse() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["baseline", "fixed", "graphed"], default="baseline")
    ap.add_argument("--mode", choices=["time", "profile", "nsys", "syncdebug", "capture"], default="time")
    ap.add_argument("--d", type=int, default=384, help="model width")
    ap.add_argument("--layers", type=int, default=6)
    ap.add_argument("--vocab", type=int, default=4096)
    ap.add_argument("--seq", type=int, default=256)
    ap.add_argument("--batch", type=int, default=8, help="sequences per micro-batch")
    ap.add_argument("--micro", type=int, default=4, help="micro-batches per step (gradient accumulation)")
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--capture-steps", type=int, default=2)
    ap.add_argument("--trace", default="", help="profile mode: write the chrome trace here")
    ap.add_argument("--seed", type=int, default=4)
    return ap.parse_args()


class Block(torch.nn.Module):
    def __init__(self, d: int):
        super().__init__()
        self.ln = torch.nn.LayerNorm(d)
        self.up = torch.nn.Linear(d, 4 * d)
        self.down = torch.nn.Linear(4 * d, d)

    def forward(self, x):
        return x + self.down(F.gelu(self.up(self.ln(x))))


class TinyLM(torch.nn.Module):
    def __init__(self, vocab: int, d: int, layers: int):
        super().__init__()
        self.emb = torch.nn.Embedding(vocab, d)
        self.blocks = torch.nn.ModuleList(Block(d) for _ in range(layers))
        self.ln = torch.nn.LayerNorm(d)
        self.head = torch.nn.Linear(d, vocab)

    def forward(self, tok):
        x = self.emb(tok)
        for b in self.blocks:
            x = b(x)
        return self.head(self.ln(x))


def make_batches(a, n: int):
    """n micro-batches of (tokens, targets, attention_mask) in pinned host memory; padding at the end of each row."""
    g = torch.Generator().manual_seed(a.seed)
    out = []
    for _ in range(n):
        tok = torch.randint(0, a.vocab, (a.batch, a.seq), generator=g)
        lengths = torch.randint(a.seq // 2, a.seq + 1, (a.batch,), generator=g)
        mask = (torch.arange(a.seq)[None, :] < lengths[:, None])
        out.append((tok.pin_memory(), torch.roll(tok, -1, 1).pin_memory(), mask.pin_memory()))
    return out


def loss_baseline(logits, tgt, mask):
    per_token = F.cross_entropy(logits.float().flatten(0, 1), tgt.flatten(), reduction="none").view_as(tgt)
    loss = per_token[mask].mean()                 # boolean indexing: data-dependent shape -> host sync
    if not torch.isfinite(loss):                  # Python branch on a GPU value -> host sync
        raise FloatingPointError("non-finite loss")
    return loss


def loss_fixed(logits, tgt, mask):
    per_token = F.cross_entropy(logits.float().flatten(0, 1), tgt.flatten(), reduction="none").view_as(tgt)
    masked = torch.where(mask, per_token, torch.zeros_like(per_token))   # static shapes, NaN-safe at padding
    return masked.sum() / mask.sum().clamp_min(1)


class Trainer:
    def __init__(self, a):
        torch.manual_seed(a.seed)
        self.a = a
        self.model = TinyLM(a.vocab, a.d, a.layers).cuda()
        graphed = a.variant == "graphed" or a.mode == "capture"
        self.opt = torch.optim.AdamW(self.model.parameters(), lr=1e-4, foreach=True, capturable=graphed)
        self.host = make_batches(a, 8 * a.micro)
        self.i = 0
        self.loss_fn = loss_baseline if a.variant == "baseline" else loss_fixed
        # static device buffers for the micro-batches of one step (the graph needs fixed addresses)
        self.dev = [(torch.empty_like(t, device="cuda"), torch.empty_like(y, device="cuda"), torch.empty_like(m, device="cuda"))
                    for t, y, m in self.host[: a.micro]]
        self.bad = torch.zeros((), dtype=torch.bool, device="cuda")
        self.graph = None

    def load(self):
        """Copy the next step's micro-batches into the static device buffers (pinned, non_blocking)."""
        for k in range(self.a.micro):
            src = self.host[(self.i * self.a.micro + k) % len(self.host)]
            for d, s in zip(self.dev[k], src):
                d.copy_(s, non_blocking=True)
        self.i += 1

    def compute(self, loss_fn=None):
        loss_fn = loss_fn or self.loss_fn
        total = torch.zeros((), device="cuda")
        for k in range(self.a.micro):
            tok, tgt, mask = self.dev[k]
            with torch.autocast("cuda", dtype=torch.bfloat16, cache_enabled=False):
                logits = self.model(tok)
            loss = loss_fn(logits, tgt, mask) / self.a.micro
            loss.backward()
            total += loss.detach()
        self.opt.step()
        self.opt.zero_grad(set_to_none=False)
        if self.a.variant != "baseline":
            self.bad |= ~torch.isfinite(total)          # NaN guard on the GPU; read once per step, after it
        return total

    def capture(self):
        """Whole-step CUDA Graph capture (PyTorch 'whole network capture' recipe)."""
        s = torch.cuda.Stream()
        s.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(s):
            for _ in range(3):                           # warm up on a side stream before capture
                self.compute()
        torch.cuda.current_stream().wait_stream(s)
        self.graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(self.graph):
            self.static_total = self.compute()

    def step(self):
        self.load()
        if self.a.variant == "graphed":
            if self.graph is None:
                self.capture()
            self.graph.replay()
            total = self.static_total
        else:
            total = self.compute()
        return total

    def end_of_step(self):
        # Fixed variants read the GPU NaN flag here: the copy is queued behind all of the step's work, so the
        # read is the end-of-step wait itself and adds no idle gap. Then synchronize, which closes the step
        # window over all GPU work (Section 4.10 pitfall).
        bad = self.a.variant != "baseline" and bool(self.bad)
        torch.cuda.synchronize()
        if bad:
            raise FloatingPointError("non-finite loss")


def tokens_per_step(a) -> int:
    return a.batch * a.seq * a.micro


def mode_time(tr, a):
    times = []
    for i in range(a.warmup + a.steps):
        t0 = time.perf_counter()
        tr.step()
        tr.end_of_step()
        if i >= a.warmup:
            times.append((time.perf_counter() - t0) * 1e3)
    med = statistics.median(times)
    print(json.dumps({"variant": a.variant, "median_ms": med, "p95_ms": sorted(times)[int(0.95 * (len(times) - 1))],
                      "min_ms": min(times), "max_ms": max(times), "steps": len(times), "warmup": a.warmup,
                      "tokens_per_s": tokens_per_step(a) / (med / 1e3), "batch": a.batch, "micro": a.micro, "seq": a.seq,
                      "step_ms": times}))


RUNTIME_SYNC = ("cudaStreamSynchronize", "cudaDeviceSynchronize", "cudaEventSynchronize")
LAUNCH = ("cudaLaunchKernel", "cudaLaunchKernelExC", "cuLaunchKernel", "cudaGraphLaunch")


def mode_profile(tr, a):
    """Count runtime calls and aten ops per step, inside the step body only.

    The step body (load + forward/backward/optimizer, or the graph replay) runs inside a record_function range;
    the end-of-step synchronize and the fixed variants' NaN-flag read come after it, once the GPU has drained,
    and are counted separately (`end_of_step_*`), so `syncs_per_step` is the syncs the step itself forces."""
    from torch.profiler import ProfilerActivity, profile, record_function
    for _ in range(a.warmup):
        tr.step()
        tr.end_of_step()
    n = 3
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        for _ in range(n):
            with record_function("ch04_step_body"):
                tr.step()
            tr.end_of_step()
    evs = prof.events()
    bodies = [(e.time_range.start, e.time_range.end) for e in evs if e.name == "ch04_step_body"]

    def in_body(e):
        return any(s <= e.time_range.start and e.time_range.end <= t for s, t in bodies)
    body = [e.name for e in evs if e.name != "ch04_step_body" and in_body(e)]
    rest = [e.name for e in evs if e.name != "ch04_step_body" and not in_body(e)]

    def per_step(names, pred):
        return sum(1 for x in names if pred(x)) / n
    out = {
        "variant": a.variant, "profiled_steps": n, "step_body_ranges": len(bodies),
        "device_events": sum(1 for e in evs if str(e.device_type).endswith("CUDA")),
        "launches_per_step": per_step(body, lambda x: x in LAUNCH),
        "graph_launches_per_step": per_step(body, lambda x: x == "cudaGraphLaunch"),
        "syncs_per_step": per_step(body, lambda x: x in RUNTIME_SYNC),
        "memcpy_per_step": per_step(body, lambda x: x == "cudaMemcpyAsync"),
        "local_scalar_dense_per_step": per_step(body, lambda x: x == "aten::_local_scalar_dense"),
        "nonzero_per_step": per_step(body, lambda x: x == "aten::nonzero"),
        "is_nonzero_per_step": per_step(body, lambda x: x == "aten::is_nonzero"),
        "aten_ops_per_step": per_step(body, lambda x: x.startswith("aten::")),
        "end_of_step_syncs_per_step": per_step(rest, lambda x: x in RUNTIME_SYNC),
        "end_of_step_local_scalar_dense_per_step": per_step(rest, lambda x: x == "aten::_local_scalar_dense"),
    }
    if a.trace:
        prof.export_chrome_trace(a.trace)
    table = prof.key_averages().table(sort_by="self_cpu_time_total", row_limit=15)
    print(table, file=sys.stderr)
    print(json.dumps(out))


def mode_nsys(tr, a):
    for _ in range(a.warmup):
        tr.step()
        tr.end_of_step()
    torch.cuda.profiler.start()
    for i in range(a.capture_steps):
        with torch.cuda.nvtx.range(f"train_step_{i}"):
            tr.step()
            tr.end_of_step()                             # inside the range, so the window covers the GPU work
    torch.cuda.profiler.stop()
    print(json.dumps({"variant": a.variant, "captured_steps": a.capture_steps}))


def mode_syncdebug(tr, a):
    for _ in range(2):
        tr.step()
        tr.end_of_step()
    torch.cuda.synchronize()
    torch.cuda.set_sync_debug_mode("warn")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        tr.load()
        tr.compute()
    torch.cuda.set_sync_debug_mode("default")
    torch.cuda.synchronize()
    import traceback  # noqa: F401  (the warning text already carries the stack)
    lines = [str(x.message) for x in w]
    for x in w:
        print(f"WARNING {x.filename}:{x.lineno}: {x.message}")
    print(json.dumps({"variant": a.variant, "sync_warnings": len(lines)}))


def mode_capture(tr, a):
    """Try to capture the baseline step (with its host syncs) as a CUDA Graph.

    During capture nothing executes, so a host read of a GPU value cannot return a real value: either CUDA
    rejects the synchronizing call, or the read returns garbage and the code acts on it. Both are recorded,
    with the whole exception chain (the error raised when the broken capture is closed is chained to it)."""
    import traceback
    try:
        tr.capture()
        ok, chain = True, []
    except Exception as e:  # noqa: BLE001 - the error text is the evidence
        ok, chain, x = False, [], e
        while x is not None and len(chain) < 5:
            chain.append(f"{type(x).__name__}: {str(x).strip().splitlines()[0] if str(x).strip() else ''}")
            x = x.__cause__ or x.__context__
        traceback.print_exc(file=sys.stderr)
    print(json.dumps({"variant": a.variant, "capture_succeeded": ok, "error": chain[0] if chain else "",
                      "error_chain": chain}))


def main() -> int:
    a = parse()
    if not torch.cuda.is_available():
        print("no CUDA device", file=sys.stderr)
        return 2
    if a.mode == "capture":
        a.variant = "baseline"
    tr = Trainer(a)
    {"time": mode_time, "profile": mode_profile, "nsys": mode_nsys, "syncdebug": mode_syncdebug,
     "capture": mode_capture}[a.mode](tr, a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
