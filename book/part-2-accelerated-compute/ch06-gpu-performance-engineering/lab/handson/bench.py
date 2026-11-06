#!/usr/bin/env python3
"""Ch 6 hands-on: ONE benchmark run (one fresh process) of one arm. Prints one JSON line.

The workload is one training step of a small MLP (BF16 autocast, AdamW). The arms differ only in the
variable under test:
  base    AdamW(foreach=True)  - the baseline
  aa      identical to base    - the A/A arm: same code, a separate group of runs
  fused   AdamW(fused=True)    - the candidate change
  zero    base, but zero_grad(set_to_none=False) - a second candidate (writes zeros instead of freeing)

Every iteration is timed with CUDA events (Section 6.6, "Timing method") and the first --warmup iterations are
recorded but flagged, so the warm-up effect is visible in the raw data and excluded by the protocol.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

import torch

ARMS = {"base": "AdamW foreach (baseline)", "aa": "AdamW foreach (A/A group)", "fused": "AdamW fused",
        "zero": "AdamW foreach, zero_grad(set_to_none=False)"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=sorted(ARMS), required=True)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--iters", type=int, default=50)
    ap.add_argument("--d", type=int, default=1024)
    ap.add_argument("--blocks", type=int, default=4)
    ap.add_argument("--tokens", type=int, default=4096)
    a = ap.parse_args()
    t_start = time.time()
    torch.manual_seed(6)
    layers = []
    for _ in range(a.blocks):
        layers += [torch.nn.Linear(a.d, 4 * a.d), torch.nn.GELU(), torch.nn.Linear(4 * a.d, a.d)]
    model = torch.nn.Sequential(*layers).cuda()
    if a.arm == "fused":
        opt = torch.optim.AdamW(model.parameters(), lr=1e-4, fused=True)
    else:
        opt = torch.optim.AdamW(model.parameters(), lr=1e-4, foreach=True)
    set_to_none = a.arm != "zero"
    x = torch.randn(a.tokens, a.d, device="cuda")

    def step():
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = model(x).float().pow(2).mean()
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=set_to_none)

    ms = []
    t_loop = time.time()
    for _ in range(a.warmup + a.iters):
        e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        e0.record()
        step()
        e1.record()
        e1.synchronize()
        ms.append(e0.elapsed_time(e1))
    print(json.dumps({"arm": a.arm, "what": ARMS[a.arm], "warmup": a.warmup, "iters": a.iters, "ms": ms,
                      "t_start": t_start, "t_loop": t_loop, "t_end": time.time(), "torch": torch.__version__,
                      "params": sum(p.numel() for p in model.parameters()), "d": a.d, "blocks": a.blocks,
                      "tokens": a.tokens}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
