#!/usr/bin/env python3
"""Ch 22 hands-on: name the bottleneck from evidence, with rules written down before the runs.

    python3 diagnose.py evidence.json healthy.json      -> prints one JSON line {"verdict": ..., "why": [...]}

The rules follow the step equation (Section 22.1): first ask the workload's own clock where the time went
(data wait or not), then use the layer evidence to split the data-wait branch. Each rule is a discriminating
test: the competing hypotheses predict different values for it (Section 22.3).

  slower than healthy by < 10 %                               -> none
  data-wait share < 15 % of the step:
      synchronize calls inside the step (torch.profiler)      -> host_sync
      otherwise                                               -> compute_or_other
  data-wait share >= 15 % (the GPU is waiting for input):
      batches decoded inside the training process itself     -> dataloader   (no parallel decode)
      decode threads wait for a CPU > 25 % of their decode    -> cpu_contention (run-queue delay)
      workers wait on the network > 2 x healthy fetch and
        that wait exceeds 25 % of the decode time            -> network
      otherwise                                               -> dataloader   (decode throughput too low)
"""
from __future__ import annotations

import json
import sys


def diagnose(ev: dict, healthy: dict) -> dict:
    why = []
    slow = ev["step_ms"] / healthy["step_ms"]
    why.append(f"step {ev['step_ms']:.1f} ms vs healthy {healthy['step_ms']:.1f} ms ({slow:.2f}x)")
    if slow < 1.10:
        return {"verdict": "none", "slowdown": slow, "why": why}
    dw = ev["data_wait_share"]
    why.append(f"data-wait share {100 * dw:.0f} % (healthy {100 * healthy['data_wait_share']:.0f} %)")
    if dw < 0.15:
        syncs = ev.get("profile_syncs_per_step")
        why.append(f"synchronize calls per step: {syncs} (healthy {healthy.get('profile_syncs_per_step')})")
        if syncs is not None and syncs >= 1 and syncs > (healthy.get("profile_syncs_per_step") or 0):
            return {"verdict": "host_sync", "slowdown": slow, "why": why}
        return {"verdict": "compute_or_other", "slowdown": slow, "why": why}
    if ev["loader_pids"] == [ev["pid"]]:
        why.append(f"batches decoded by the training process itself (pid {ev['pid']}); main-thread CPU {100 * ev['main_cpu_share']:.0f} %")
        return {"verdict": "dataloader", "slowdown": slow, "why": why}
    rq = ev["decode_runqueue_share"]
    why.append(f"decode run-queue delay {100 * rq:.0f} % of decode time (healthy {100 * healthy['decode_runqueue_share']:.0f} %)")
    if rq > 0.25:
        return {"verdict": "cpu_contention", "slowdown": slow, "why": why}
    fw, hf = ev["fetch_wait_ms_median"], max(healthy["fetch_wait_ms_median"], 0.1)
    why.append(f"worker network wait {fw:.1f} ms per batch (healthy {hf:.1f} ms), decode {ev['decode_ms_median']:.1f} ms")
    if fw > 2 * hf and fw > 0.25 * ev["decode_ms_median"]:
        return {"verdict": "network", "slowdown": slow, "why": why}
    return {"verdict": "dataloader", "slowdown": slow, "why": why}


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    ev = json.loads(open(sys.argv[1]).read().strip().splitlines()[-1])
    healthy = json.loads(open(sys.argv[2]).read().strip().splitlines()[-1])
    print(json.dumps(diagnose(ev, healthy)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
