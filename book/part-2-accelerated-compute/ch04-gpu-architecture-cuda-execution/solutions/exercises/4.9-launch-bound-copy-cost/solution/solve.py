"""Exercise 4.9: launch-bound loop, CUDA Graph replay, and the input copy on the critical path.

Usage: python solve.py --out DIR
Inputs (prompt): 400 kernels/iteration, 6 µs GPU each, 10 µs CPU per launch; graph replay 15 µs CPU and
1 µs between kernels on the GPU; 256 MiB input; pageable 12 GB/s, pinned 50 GB/s.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

N, GPU_US, CPU_US = 400, 6.0, 10.0
REPLAY_US, INTER_US = 15.0, 1.0
INPUT_B = 256 * 2**20
PAGEABLE_BPS, PINNED_BPS = 12e9, 50e9
KEY = {"eager_ms": 4.0, "busy_eager": 0.60, "graph_ms": 2.814, "pageable_ms": 22.4,
       "pinned_ms": 5.37, "steady_ms": 5.37}  # exercises-key.md 4.9
KEY_SPEEDUP = 1.42
TOL = 0.005  # relative


def close(a: float, b: float) -> bool:
    return abs(a - b) <= TOL * abs(b)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    gpu_ms = N * GPU_US / 1e3
    # (a) Eager: the CPU issues one launch per 10 µs, each kernel needs 6 µs, so the GPU drains the queue
    # faster than it fills; the iteration is the CPU issue time (the last kernel's 6 µs tail is negligible).
    eager_ms = max(N * CPU_US, N * GPU_US) / 1e3
    busy = gpu_ms / eager_ms
    # (b) Graph: one 15 µs replay call, then 400 kernels with 1 µs spacing on the GPU.
    graph_ms = (REPLAY_US + N * GPU_US + (N - 1) * INTER_US) / 1e3
    speedup = eager_ms / graph_ms
    busy_g = gpu_ms / graph_ms
    # (c) Copies.
    pageable_ms = INPUT_B / PAGEABLE_BPS * 1e3
    pinned_ms = INPUT_B / PINNED_BPS * 1e3
    eager_pageable_ms = pageable_ms + eager_ms   # serial and host-blocking
    steady_ms = max(graph_ms, pinned_ms)         # pinned copy prefetched one iteration ahead on a side stream
    got = {"eager_ms": eager_ms, "busy_eager": busy, "graph_ms": graph_ms, "pageable_ms": pageable_ms,
           "pinned_ms": pinned_ms, "steady_ms": steady_ms}
    for k, v in got.items():
        assert close(v, KEY[k]), (k, v)
    assert abs(speedup - KEY_SPEEDUP) < 0.01, speedup
    assert pinned_ms > graph_ms, "key conclusion: the steady state is copy-bound"
    res = {"exercise": "4.9", "evidence_label": "MODELED",
           "inputs": {"kernels": N, "gpu_us": GPU_US, "cpu_us_per_launch": CPU_US, "graph_replay_us": REPLAY_US,
                      "graph_inter_kernel_us": INTER_US, "input_bytes": INPUT_B, "pageable_Bps": PAGEABLE_BPS,
                      "pinned_Bps": PINNED_BPS},
           "answer": {"a_eager_iteration_ms": round(eager_ms, 3), "a_kernel_busy": round(busy, 3),
                      "b_graph_iteration_ms": round(graph_ms, 3), "b_speedup": round(speedup, 3),
                      "b_kernel_busy": round(busy_g, 3), "c_pageable_copy_ms": round(pageable_ms, 2),
                      "c_eager_with_pageable_ms": round(eager_pageable_ms, 2), "c_pinned_copy_ms": round(pinned_ms, 2),
                      "c_steady_state_iteration_ms": round(steady_ms, 2), "c_bound": "PCIe copy"},
           "units": {"time": "ms", "busy": "fraction"}}
    (out / "result.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Exercise 4.9 — launch-bound loop and copy cost `[MODELED]`

(a) Eager: iteration = max(400 × 10 µs, 400 × 6 µs) = {eager_ms:.1f} ms (CPU-limited);
kernel-busy = 2.4 / {eager_ms:.1f} = {busy * 100:.0f} %.

(b) CUDA Graph: 15 + 400 × 6 + 399 × 1 = {graph_ms * 1e3:,.0f} µs = {graph_ms:.2f} ms;
speedup {eager_ms:.1f} / {graph_ms:.3f} = {speedup:.2f}×; kernel-busy {busy_g * 100:.0f} %.

(c) Input 256 MiB = {INPUT_B:,} B.
Pageable: {INPUT_B:,} B / 12 × 10⁹ B/s = {pageable_ms:.1f} ms, serial and host-blocking, so the eager
iteration is ≈ {eager_pageable_ms:.1f} ms.
Pinned: {INPUT_B:,} B / 50 × 10⁹ B/s = {pinned_ms:.2f} ms. Prefetched on a side stream, the steady state is
max({graph_ms:.2f}, {pinned_ms:.2f}) = {steady_ms:.2f} ms: copy-bound. Reduce the bytes per iteration.
"""
    (out / "result.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
