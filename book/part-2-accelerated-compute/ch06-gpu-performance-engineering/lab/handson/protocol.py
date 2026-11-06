#!/usr/bin/env python3
"""Ch 6 hands-on: run the benchmark protocol (Table 6.5) and keep every raw sample.

    python3 protocol.py OUTDIR [--arms base,aa,fused,zero] [--runs 8] [--iters 50] [--warmup 5]

- every run is a fresh process (`bench.py`), so process-level state (allocator, cuBLAS heuristics, clocks at
  start) varies between runs the way it does between jobs: runs are the unit of replication;
- arms are interleaved round-robin and the start rotates every round (ABCD, BCDA, CDAB, ...), so drift
  (heat, other tenants) spreads over all arms instead of landing on one;
- nvidia-smi samples SM clock, memory clock, temperature, power and clock-event reasons every 100 ms for the
  whole session (telemetry.csv), so each run can be judged against its peers afterwards.

Writes OUTDIR/runs.jsonl (one line per run, every iteration's time), OUTDIR/telemetry.csv, OUTDIR/schedule.txt.
Run it while holding the GPU lock: the protocol assumes a dedicated GPU.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TELEMETRY = ("timestamp,clocks.sm,clocks.mem,temperature.gpu,power.draw,utilization.gpu,"
             "clocks_event_reasons.active,clocks_event_reasons.sw_power_cap,clocks_event_reasons.hw_slowdown,"
             "clocks_event_reasons.sw_thermal_slowdown,clocks_event_reasons.hw_thermal_slowdown")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--arms", default="base,aa,fused,zero")
    ap.add_argument("--runs", type=int, default=8)
    ap.add_argument("--iters", type=int, default=50)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    arms = a.arms.split(",")
    schedule = []
    for r in range(a.runs):
        k = r % len(arms)
        schedule += [(r + 1, arm) for arm in arms[k:] + arms[:k]]
    (out / "schedule.txt").write_text("\n".join(f"{r} {arm}" for r, arm in schedule) + "\n")
    tel = open(out / "telemetry.csv", "w")
    sampler = subprocess.Popen(["nvidia-smi", f"--query-gpu={TELEMETRY}", "--format=csv", "-lms", "100", "-i", "0"],
                               stdout=tel)
    try:
        with open(out / "runs.jsonl", "w") as f:
            for order, (r, arm) in enumerate(schedule, 1):
                res = subprocess.run([a.python, str(HERE / "bench.py"), "--arm", arm, "--iters", str(a.iters),
                                      "--warmup", str(a.warmup)], capture_output=True, text=True, timeout=600)
                if res.returncode != 0:
                    print(res.stderr, file=sys.stderr)
                    raise SystemExit(f"run {r} of {arm} failed")
                d = json.loads(res.stdout.strip().splitlines()[-1])
                d.update({"run": r, "order": order})
                f.write(json.dumps(d) + "\n")
                f.flush()
                med = sorted(d["ms"][a.warmup:])[len(d["ms"][a.warmup:]) // 2]
                print(f"  run {order:3d}/{len(schedule)}  {arm:6s} round {r}: median {med:.3f} ms", flush=True)
    finally:
        sampler.terminate()
        sampler.wait(timeout=10)
        tel.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
