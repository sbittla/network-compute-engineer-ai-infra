#!/usr/bin/env python3
"""Chapter 2 hands-on lab: drive the GPU through power phases while nvidia-smi samples it at ~100 ms.

Phases (run.sh holds the shared GPU lock around this script):

  idle         nothing running: the floor
  memory       1 GiB device-to-device copies: DRAM-bound, few FLOPs
  compute      8192^3 BF16 GEMMs back to back: Tensor-Core-bound
  cooldown     idle again: how fast power and temperature fall
  ramp_dNN     GEMMs at duty cycle NN % (on/off in 50 ms periods, faster than the sampler): where does the power limit start to bind?
  square       1 s compute, 1 s idle, repeated: the synchronized step-boundary swing of Table 2.5
  idle_end     idle

Raw outputs in --out: ch02_telemetry.csv (samples), phases.json (start/end of each phase), counters.json
(clock-event violation counters and the enforced limit read at every phase boundary), field_availability.json,
nvidia_smi_q_{before,after}.txt and power_controls.txt (whether this platform lets you change limits or
clocks; we only *read* them, or try to set the limit to the value it already has).
"""
from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

import torch

from ch02_telemetry import Telemetry, save_json, snapshot

DEV = "cuda"


def smi(*args: str) -> str:
    r = subprocess.run(["nvidia-smi", *args], capture_output=True, text=True, timeout=60)
    return f"$ nvidia-smi {' '.join(args)}\n(exit {r.returncode})\n{r.stdout}{r.stderr}\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--quick", action="store_true", help="short phases (smoke test, not for evidence)")
    a = ap.parse_args()
    out: Path = a.out
    out.mkdir(parents=True, exist_ok=True)
    k = 0.3 if a.quick else 1.0
    durations = {"idle": 10, "memory": 25, "compute": 25, "cooldown": 12, "ramp": 8, "square_cycles": 8, "idle_end": 6}

    (out / "nvidia_smi_q_before.txt").write_text(smi("-q", "-d", "POWER,CLOCK,PERFORMANCE,TEMPERATURE"))
    # Can this platform change power limits? Setting the limit to its *current* value changes nothing
    # where it is allowed and reports the refusal where it is not (WSL2: "Insufficient Permissions").
    lim = snapshot(["power.limit", "enforced.power.limit"])
    cur = lim.get("power.limit") if isinstance(lim.get("power.limit"), float) else lim.get("enforced.power.limit")
    ctl = smi("-q", "-d", "POWER")
    if isinstance(cur, float):
        ctl += smi("-pl", f"{cur:.2f}")
    (out / "power_controls.txt").write_text(ctl)

    tel = Telemetry(out / "ch02_telemetry.csv")
    save_json(tel.availability, out / "field_availability.json")
    phases: dict[str, list[float]] = {}
    counters: dict[str, dict] = {}

    n = 8192
    A = torch.randn(n, n, device=DEV, dtype=torch.bfloat16)
    B = torch.randn(n, n, device=DEV, dtype=torch.bfloat16)
    a4, b4 = A[:4096, :4096].contiguous(), B[:4096, :4096].contiguous()
    x = torch.empty(256 * 2 ** 20, dtype=torch.float32, device=DEV)
    y = torch.empty_like(x)
    for _ in range(3):
        A @ B; a4 @ b4; y.copy_(x)
    torch.cuda.synchronize()
    work = {"gemm_flop": 0.0, "copy_bytes": 0.0}

    def phase(name: str, seconds: float, body, snap: bool = True) -> None:
        if snap:
            counters[f"{name}:start"] = snapshot()
        t0 = time.time()
        end = time.perf_counter() + seconds
        body(end)
        torch.cuda.synchronize()
        phases[name] = [t0, time.time()]
        if snap:
            counters[f"{name}:end"] = snapshot()

    def idle(end):
        time.sleep(max(0.0, end - time.perf_counter()))

    def memory(end):
        while time.perf_counter() < end:
            for _ in range(8):
                y.copy_(x)
            torch.cuda.synchronize()
            work["copy_bytes"] += 8 * 2 * x.numel() * 4

    def compute(end):
        while time.perf_counter() < end:
            for _ in range(4):
                A @ B
            torch.cuda.synchronize()
            work["gemm_flop"] += 4 * 2 * n ** 3

    def duty(frac: float, period: float = 0.05):
        def body(end):
            while time.perf_counter() < end:
                p0 = time.perf_counter()
                while time.perf_counter() - p0 < frac * period:
                    a4 @ b4                 # ~5 ms each at full clock: fine-grained enough for 50 ms periods
                    torch.cuda.synchronize()
                time.sleep(max(0.0, period - (time.perf_counter() - p0)))
        return body

    tel.start()
    try:
        phase("idle", k * durations["idle"], idle)
        phase("memory", k * durations["memory"], memory)
        phase("compute", k * durations["compute"], compute)
        phase("cooldown", k * durations["cooldown"], idle)
        for d in (0.25, 0.5, 0.75, 1.0):
            phase(f"ramp_d{int(d * 100):03d}", k * durations["ramp"], duty(d))
        sq_t0 = time.time()
        for i in range(durations["square_cycles"] if not a.quick else 3):
            phase(f"square_on_{i}", 1.0, compute, snap=False)
            phase(f"square_off_{i}", 1.0, idle, snap=False)
        phases["square"] = [sq_t0, time.time()]
        phase("idle_end", k * durations["idle_end"], idle)
    finally:
        tel.stop()
        save_json(phases, out / "phases.json")
        save_json(counters, out / "counters.json")
        save_json(work, out / "work.json")
    (out / "nvidia_smi_q_after.txt").write_text(smi("-q", "-d", "POWER,CLOCK,PERFORMANCE,TEMPERATURE"))
    print(f"raw outputs written to {out}")


if __name__ == "__main__":
    main()
