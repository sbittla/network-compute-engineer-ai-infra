#!/usr/bin/env python3
"""Chapter 21 hands-on lab: energy per unit of useful work, measured (run.sh holds the GPU lock).

A fixed job (a fixed number of training tokens through a small decoder-only transformer) is run under
several settings while nvidia-smi samples board power at ~100 ms. Energy is the integral of power over
the job's wall time. What we vary is what a single WSL2 laptop lets us vary:

  intensity_bB    batch size B (1, 4, 16 sequences of 512 tokens): how hard each step works the GPU
  duty_DDD        batch 16 with idle gaps after every step (busy fraction DDD %): an input stall, a
                  straggler wait, or a half-idle allocation, i.e. the goodput rung of the ladder
  cap_WWW         (only where permitted and CH21_ALLOW_POWER_CAP=1) batch 16 under power limit WWW W;
                  the original limit is restored afterwards

Raw outputs in --out: ch21_telemetry.csv, jobs.json (window, tokens, busy time per job), steps.csv,
controls.txt (which power controls this platform allows), field_availability.json, model.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

from ch21_telemetry import Telemetry, save_json, snapshot

DEV = "cuda"
CFG = dict(vocab=8192, d=768, layers=8, heads=12, seq=512)


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


def smi(*args: str) -> tuple[int, str]:
    r = subprocess.run(["nvidia-smi", *args], capture_output=True, text=True, timeout=60)
    return r.returncode, (r.stdout + r.stderr).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--quick", action="store_true", help="smaller fixed job (smoke test, not for evidence)")
    a = ap.parse_args()
    out: Path = a.out
    out.mkdir(parents=True, exist_ok=True)
    job_tokens = 2 ** 17 if a.quick else 2 ** 19          # the fixed job: 524,288 training tokens
    torch.manual_seed(0)

    # ---- which power controls does this platform allow? -------------------------------------------------
    lim = snapshot(["power.limit", "enforced.power.limit", "power.default_limit", "power.min_limit", "power.max_limit"])
    requested = lim.get("power.limit") if isinstance(lim.get("power.limit"), float) else lim.get("enforced.power.limit")
    log = [f"limits: {json.dumps(lim)}"]
    rc, txt = smi("-pl", f"{requested:.2f}")              # set to the value it already has: a no-op where allowed
    can_cap = rc == 0
    log.append(f"$ nvidia-smi -pl {requested:.2f}   (same value: tests permission, changes nothing)\n(exit {rc}) {txt}")
    can_lock = None
    if os.environ.get("CH21_PROBE_CLOCK_LOCK") == "1":
        maxc = snapshot(["clocks.max.sm"]).get("clocks.max.sm")
        rc, txt = smi("-lgc", f"0,{int(maxc)}")           # the widest range: no effective lock where allowed
        can_lock = rc == 0
        log.append(f"$ nvidia-smi -lgc 0,{int(maxc)}\n(exit {rc}) {txt}")
        rc2, txt2 = smi("-rgc")                           # and reset it straight away
        log.append(f"$ nvidia-smi -rgc\n(exit {rc2}) {txt2}")
    else:
        log.append("clock-lock probe not attempted (set CH21_PROBE_CLOCK_LOCK=1 to try nvidia-smi -lgc / -rgc)")
    (out / "controls.txt").write_text("\n".join(log) + "\n")

    # ---- model -----------------------------------------------------------------------------------------
    model = TinyGPT(**CFG).to(DEV)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, fused=True)
    n_flop = sum(q.numel() for q in model.parameters()) - model.pos.weight.numel()
    save_json({"config": CFG, "params_for_flops": n_flop, "flop_per_token_6N": 6 * n_flop,
               "job_tokens": job_tokens}, out / "model.json")

    def step(idx, tgt):
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = F.cross_entropy(model(idx).float().view(-1, CFG["vocab"]), tgt.view(-1))
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)
        return loss

    tel = Telemetry(out / "ch21_telemetry.csv")
    save_json(tel.availability, out / "field_availability.json")
    jobs: dict[str, dict] = {}
    step_rows: list[dict] = []

    def run_job(name: str, bsz: int, busy_frac: float = 1.0) -> None:
        idx = torch.randint(0, CFG["vocab"], (bsz, CFG["seq"]), device=DEV)
        tgt = torch.roll(idx, -1, dims=1)
        for _ in range(3):
            step(idx, tgt)                                # warm-up, outside the measured window
        torch.cuda.synchronize()
        time.sleep(1.0)                                   # let power settle between jobs
        n_steps = job_tokens // (bsz * CFG["seq"])
        busy = 0.0
        t0 = time.time()
        for k in range(n_steps):
            s0 = time.perf_counter()
            loss = step(idx, tgt)
            torch.cuda.synchronize()
            dt = time.perf_counter() - s0
            busy += dt
            step_rows.append({"job": name, "step": k, "step_s": dt})
            if busy_frac < 1.0:
                time.sleep(dt * (1.0 / busy_frac - 1.0))  # the stall: GPU allocated, nothing to do
        t1 = time.time()
        jobs[name] = {"batch": bsz, "target_busy_fraction": busy_frac, "steps": n_steps,
                      "tokens": n_steps * bsz * CFG["seq"], "t0": t0, "t1": t1, "wall_s": t1 - t0,
                      "busy_s": busy, "final_loss": float(loss), "limits": snapshot(["enforced.power.limit"])}

    tel.start()
    original_limit = requested
    try:
        t0 = time.time(); time.sleep(8.0 if not a.quick else 3.0)
        jobs["idle"] = {"t0": t0, "t1": time.time(), "wall_s": time.time() - t0, "tokens": 0, "busy_s": 0.0}
        for b in (1, 4, 16):
            run_job(f"intensity_b{b}", b)
        for d in (0.75, 0.5, 0.25):
            run_job(f"duty_{int(d * 100):03d}", 16, d)
        if can_cap and os.environ.get("CH21_ALLOW_POWER_CAP") == "1":
            # Only on a dedicated machine you own; restored in `finally` (and by teardown.sh).
            (out.parent / ".ch21_power_limit_changed").write_text(f"{original_limit}\n")
            lo = lim.get("power.min_limit") or 0.5 * original_limit
            for frac in (0.85, 0.7, 0.55):
                w = max(lo, round(original_limit * frac))
                smi("-pl", str(w))
                run_job(f"cap_{int(w):03d}", 16)
    finally:
        if can_cap and os.environ.get("CH21_ALLOW_POWER_CAP") == "1":
            smi("-pl", f"{original_limit:.2f}")
            (out.parent / ".ch21_power_limit_changed").unlink(missing_ok=True)
        tel.stop()
        save_json(jobs, out / "jobs.json")
        with open(out / "steps.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["job", "step", "step_s"])
            w.writeheader(); w.writerows(step_rows)
    print(f"raw outputs written to {out}")


if __name__ == "__main__":
    main()
