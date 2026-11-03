# Lab 4 L2: capture, classify and analyse a real training step (before and after the fixes)

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:53:15Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed (at capture time; see the erratum)

> **Erratum (2026-11-01) — fixed-variant trace analysis invalid, rerun pending.** The "fixed" step has no
> host sync, and the capture closed each step's CPU-side range before the GPU had drained its queue. The
> traced windows (20.1–24.0 ms) cover only ≈ 19 % of the measured 108.28 ms median step, while the same
> capture's kernel table holds ≈ 113 ms of GPU time per step. Every fixed-variant figure derived from the
> window is therefore invalid: traced step, GPU busy (any and kernels), copy overlap, idle gaps by cause,
> and the findings list. The per-op durations (kernel classification and top-kernels tables), the
> uninstrumented step-time table, the launch and sync counts and the 1.21× speedup are unaffected. The
> baseline windows (133–237 ms against a 131.15 ms median) pass the window-sanity invariant that
> `experiment.py` now enforces (traced window ≥ 90 % of the median step), and its figures stand. One
> caveat: optimizer kernels queued after the baseline's last `.item()` may also extend slightly past
> each window. `experiment.py` now synchronizes before closing each step range. The values below are
> left exactly as measured. This is the Section 4.10 pitfall, "NVTX ranges are CPU-side", caught in
> our own evidence.

## Workload

MLP of 4 blocks (d = 1024, 4d hidden), 33.6 M parameters, 4096 tokens per step, BF16 autocast, AdamW. **Baseline**: pageable batch copy, a `.item()` debug hook on every Linear, per-parameter (for-loop) AdamW. **Fixed**: pinned batch prefetched one step ahead with `non_blocking=True`, no hook, fused AdamW.

## Step time, uninstrumented (Chapter 6 protocol)

| Variant | n | Median (ms) | p95 (ms) | IQR (ms) | min-max (ms) | Optimizer step alone, median (p95) ms | Kernel launches / step | Host syncs / step |
|---|---|---|---|---|---|---|---|---|
| baseline | 10 | 131.15 | 145.46 | 8.99 | 128.72-145.46 | 20.793 (23.174) | 232 | 11 |
| fixed | 10 | 108.28 | 116.25 | 6.38 | 65.48-116.25 | 16.527 (17.907) | 83 | 2 |

Speed-up from the fixes: **1.21x** `[MEASURED]`. Launch and sync counts are from torch.profiler's CUDA runtime records (CPU side) over one step; the sync count includes the capture's own closing synchronize.

## Trace analysis: baseline (3 captures x 2 steps, lab `analyze()`)

| Metric | Median | min-max over steps |
|---|---|---|
| traced step (ms) | 166.5 | 133.3-237.4 |
| GPU busy, any activity | 88.0 % | 76.1-91.9 % |
| GPU busy, kernels | 81.6 % | 70.7-88.7 % |
| copy overlapped with compute | 0.0 % | 0.0-0.0 % |
| idle gaps by cause (ms/step, median) | dependency 3.91, host_sync 2.49, launch_bound 25.06 | |

Kernel classification (GPU time per step, capture 1):

| Category | Ops / step | GPU ms / step | Share | Achieved TFLOP/s | Achieved GB/s |
|---|---|---|---|---|---|
| gemm | 23 | 78.00 | 53.8 % | 10.13 | 14.8 |
| elementwise | 178 | 43.00 | 29.6 % | 0.01 | 82.4 |
| cast/copy | 43 | 10.68 | 7.4 % | 0.02 | 91.9 |
| memcpy | 25 | 7.26 | 5.0 % | 0.00 | 2.3 |
| reduction | 17 | 6.09 | 4.2 % | 0.00 | 85.4 |

Findings (capture 1, ranked by estimated saving):

1. **LAUNCH_BOUND** ≈ 14.55 ms/step — 91 kernels/step shorter than 10 µs (median 4.1 µs, grid size not captured on a 24-SM GPU); 14 launch-bound gaps/step totalling 14.55 ms
2. **PAGEABLE_H2D** ≈ 4.99 ms/step — 2 large copies from pageable memory, 32 MiB, 10.0 ms total at 3.4 GB/s (no pinned copy in this capture); host thread blocked and no kernel overlaps them
3. **STREAM_DEPENDENCY** ≈ 3.37 ms/step — 13 gap(s)/step totalling 3.37 ms where the next kernel (aten::_to_copy) had been submitted long before the GPU went idle: the compute stream was waiting on an event from another stream
4. **EXCESS_SYNC** ≈ 1.34 ms/step — 5 host-sync gaps per step, 1.34 ms GPU idle per step; the CPU blocks on .item()/synchronize and the GPU drains before new work arrives

Top kernels by GPU time (roof fraction vs this GPU's BF16 peak / DRAM bandwidth; occupancy not captured):

| Op | Count | Total (ms) | Share | Bound | % of roof |
|---|---|---|---|---|---|
| aten::mm | 30 | 94.91 | 34.4 % | compute | 28 % |
| aten::addmm | 16 | 61.08 | 22.2 % | compute | 24 % |
| aten::mul_ | 64 | 22.54 | 8.2 % | memory | 9 % |
| aten::_to_copy | 86 | 21.37 | 7.8 % | memory | 36 % |
| aten::addcdiv_ | 32 | 14.19 | 5.1 % | memory | 22 % |
| aten::add_ | 80 | 11.67 | 4.2 % | memory | 18 % |

## Trace analysis: fixed (3 captures x 2 steps, lab `analyze()`)

> **Invalid (truncated window; see the erratum).** The window-derived rows and the findings below are kept
> as measured, but they must not be cited. Only the per-op tables are usable.

| Metric | Median | min-max over steps |
|---|---|---|
| traced step (ms) | 20.5 | 20.1-24.0 |
| GPU busy, any activity | 97.2 % | 90.9-99.8 % |
| GPU busy, kernels | 97.0 % | 85.7-99.8 % |
| copy overlapped with compute | 100.0 % | 24.6-100.0 % |
| idle gaps by cause (ms/step, median) | dependency 0.58, launch_bound 0.39 | |

Kernel classification (GPU time per step, capture 1):

| Category | Ops / step | GPU ms / step | Share | Achieved TFLOP/s | Achieved GB/s |
|---|---|---|---|---|---|
| gemm | 23 | 75.08 | 66.6 % | 10.53 | 15.4 |
| elementwise | 28 | 28.62 | 25.4 % | 0.01 | 53.9 |
| cast/copy | 35 | 5.06 | 4.5 % | 0.02 | 94.6 |
| reduction | 9 | 2.09 | 1.9 % | 0.00 | 88.3 |
| memcpy | 1 | 1.64 | 1.5 % | 0.00 | 10.2 |
| optimizer | 1 | 0.29 | 0.3 % | 0.00 | 0.0 |

Findings (capture 1, ranked by estimated saving):

1. **LAUNCH_BOUND** ≈ 0.20 ms/step — 24 kernels/step shorter than 10 µs (median 5.3 µs, grid size not captured on a 24-SM GPU); 0 launch-bound gaps/step totalling 0.20 ms

Top kernels by GPU time (roof fraction vs this GPU's BF16 peak / DRAM bandwidth; occupancy not captured):

| Op | Count | Total (ms) | Share | Bound | % of roof |
|---|---|---|---|---|---|
| aten::mm | 30 | 96.00 | 43.2 % | compute | 28 % |
| aten::addmm | 16 | 54.15 | 24.4 % | compute | 27 % |
| aten::_fused_adamw_ | 2 | 36.07 | 16.2 % | memory | 12 % |
| aten::_to_copy | 70 | 10.11 | 4.5 % | memory | 37 % |
| aten::gelu_backward | 8 | 9.01 | 4.1 % | memory | 35 % |
| aten::gelu | 8 | 5.24 | 2.4 % | memory | 40 % |

Device file: NVIDIA GeForce RTX 4060 Laptop GPU, CC 8.9, 24 SMs, BF16 peak 38.2 TFLOP/s, DRAM 256 GB/s, PCIe 15.75 GB/s per direction `[MODELED from VENDOR-SPEC]`. The manuscript's worked example is an H100-class GPU (132 SMs, 989 TFLOP/s, 3.35 TB/s, Gen5 x16): **this is a laptop Ada GPU, not an H100**, so the absolute times differ; the pathologies and their signatures in the timeline are the same.

## What to conclude

- The baseline's gaps are named by their causes: the pageable copy blocks the host and cannot overlap, every `.item()` drains the queue (host_sync gaps), and the per-parameter optimizer issues bursts of tiny kernels that the GPU retires faster than the CPU can launch them (launch_bound gaps).
- The fixes remove the first two findings outright and shrink the third; the uninstrumented step-time ratio is the number to report, not the traced one (the tracer itself costs host time per op).
- `GPU busy` is not efficiency (Section 4.9): read it next to the roof fractions of the top kernels.
- A roof fraction above 100 % (for example GELU on a 16 MiB activation) is not a measurement error in the time: the working set fits in this GPU's 32 MiB L2, so the bytes never reached DRAM (exercise 6.3's mechanism). Only kernels larger than 2x L2 are held to the DRAM bound in check(), and only for the bytes beyond one L2's worth, since that much of the footprint can still hit in cache.
- Small STREAM_DEPENDENCY gaps (tens of µs) show up in both variants; part of each is the tracer's own event-record commands on the stream, so they are reported but not acted on.

## Not runnable on this host (probed, not faked)

| Part | Probe | Needs | Used instead |
|---|---|---|---|
| GPU activity in torch.profiler / nsys (CUPTI kernel and memcpy records: launch config, registers, shared memory) | torch.profiler with ProfilerActivity.CUDA over one step: 0 device events (232 cudaLaunchKernel calls recorded on the CPU side) | CUPTI activity tracing (native Linux driver; not delivered under WSL2 here), Nsight Compute for counters | CUDA-event tracer per aten op; occupancy / LOW_OCCUPANCY not evaluated |

- Step time = median of >= 5 uninstrumented steps (CUDA events) after warm-up; the traced captures are separate.
- 3 captures of 2 steps per variant; analyze() runs on each and the spread is reported.
- Tracer overhead (~10-30 us host time per op) inflates launch-bound gaps; FLOPs/bytes per op are [MODELED].
- Pageable vs pinned and the per-layer .item() are deliberate pathologies of the baseline step.
