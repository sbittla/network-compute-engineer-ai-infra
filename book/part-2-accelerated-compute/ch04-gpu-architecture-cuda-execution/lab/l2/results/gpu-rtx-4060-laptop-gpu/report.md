# Lab 4 L2: capture, classify and analyse a real training step (before and after the fixes)

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:37:19Z.

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
**Invariants:** FAILED: baseline capture lacks ['EXCESS_SYNC']: the pathologies it contains on purpose were not detected; baseline capture lacks ['EXCESS_SYNC']: the pathologies it contains on purpose were not detected

## Workload

MLP of 4 blocks (d = 1024, 4d hidden), 33.6 M parameters, 4096 tokens per step, BF16 autocast, AdamW. **Baseline**: pageable batch copy, a `.item()` debug hook on every Linear, per-parameter (for-loop) AdamW. **Fixed**: pinned batch prefetched one step ahead with `non_blocking=True`, no hook, fused AdamW.

## Step time, uninstrumented (Chapter 6 protocol)

| Variant | n | Median (ms) | p95 (ms) | IQR (ms) | min-max (ms) | Optimizer step alone, median (p95) ms | Kernel launches / step | Host syncs / step |
|---|---|---|---|---|---|---|---|---|
| baseline | 10 | 49.65 | 52.31 | 1.46 | 49.17-52.31 | 7.928 (8.159) | 232 | 11 |
| fixed | 10 | 39.39 | 39.77 | 0.25 | 39.17-39.77 | 6.581 (7.030) | 83 | 2 |

Speed-up from the fixes: **1.26x** `[MEASURED]`. Launch and sync counts are from torch.profiler's CUDA runtime records (CPU side) over one step; the sync count includes the capture's own closing synchronize.

## Trace analysis: baseline (3 captures x 2 steps, lab `analyze()`)

| Metric | Median | min-max over steps |
|---|---|---|
| traced step (ms) | 62.3 | 54.9-68.0 |
| GPU busy, any activity | 88.0 % | 86.2-93.2 % |
| GPU busy, kernels | 81.5 % | 78.9-87.0 % |
| copy overlapped with compute | 0.0 % | 0.0-0.0 % |
| idle gaps by cause (ms/step, median) | dependency 0.75, host_sync 0.08, launch_bound 4.70 | |

Kernel classification (GPU time per step, capture 1):

| Category | Ops / step | GPU ms / step | Share | Achieved TFLOP/s | Achieved GB/s |
|---|---|---|---|---|---|
| gemm | 23 | 27.28 | 48.1 % | 28.97 | 42.4 |
| elementwise | 178 | 18.18 | 32.1 % | 0.03 | 194.7 |
| cast/copy | 43 | 4.66 | 8.2 % | 0.04 | 210.8 |
| memcpy | 25 | 4.40 | 7.8 % | 0.00 | 3.8 |
| reduction | 17 | 2.14 | 3.8 % | 0.00 | 242.9 |

Findings (capture 1, ranked by estimated saving):

1. **STREAM_DEPENDENCY** ≈ 5.75 ms/step — 98 gap(s)/step totalling 5.75 ms where the next kernel (aten::_to_copy) had been submitted long before the GPU went idle: the compute stream was waiting on an event from another stream
2. **PAGEABLE_H2D** ≈ 3.24 ms/step — 2 large copies from pageable memory, 32 MiB, 6.5 ms total at 5.2 GB/s (no pinned copy in this capture); host thread blocked and no kernel overlaps them
3. **LAUNCH_BOUND** ≈ 2.18 ms/step — 54 kernels/step shorter than 10 µs (median 3.8 µs, grid size not captured on a 24-SM GPU); 7 launch-bound gaps/step totalling 2.18 ms

Top kernels by GPU time (roof fraction vs this GPU's BF16 peak / DRAM bandwidth; occupancy not captured):

| Op | Count | Total (ms) | Share | Bound | % of roof |
|---|---|---|---|---|---|
| aten::mm | 30 | 34.79 | 33.3 % | compute | 78 % |
| aten::addmm | 16 | 19.77 | 18.9 % | compute | 73 % |
| aten::_to_copy | 86 | 9.32 | 8.9 % | memory | 82 % |
| aten::abs | 16 | 8.02 | 7.7 % | memory | 65 % |
| aten::mul_ | 64 | 5.67 | 5.4 % | memory | 37 % |
| aten::addcdiv_ | 32 | 4.32 | 4.1 % | memory | 73 % |

## Trace analysis: fixed (3 captures x 2 steps, lab `analyze()`)

| Metric | Median | min-max over steps |
|---|---|---|
| traced step (ms) | 23.0 | 16.8-33.2 |
| GPU busy, any activity | 99.6 % | 93.1-99.7 % |
| GPU busy, kernels | 99.3 % | 90.6-99.6 % |
| copy overlapped with compute | 95.4 % | 49.0-99.3 % |
| idle gaps by cause (ms/step, median) | dependency 0.02, launch_bound 0.20 | |

Kernel classification (GPU time per step, capture 1):

| Category | Ops / step | GPU ms / step | Share | Achieved TFLOP/s | Achieved GB/s |
|---|---|---|---|---|---|
| gemm | 23 | 26.73 | 65.5 % | 29.57 | 43.3 |
| elementwise | 28 | 9.95 | 24.4 % | 0.02 | 155.1 |
| cast/copy | 35 | 1.89 | 4.6 % | 0.04 | 252.7 |
| memcpy | 1 | 1.62 | 4.0 % | 0.00 | 10.4 |
| reduction | 9 | 0.57 | 1.4 % | 0.00 | 322.6 |
| optimizer | 1 | 0.02 | 0.1 % | 0.00 | 0.0 |

Findings (capture 1, ranked by estimated saving):

1. **LAUNCH_BOUND** ≈ 0.23 ms/step — 24 kernels/step shorter than 10 µs (median 5.0 µs, grid size not captured on a 24-SM GPU); 0 launch-bound gaps/step totalling 0.23 ms
2. **STREAM_DEPENDENCY** ≈ 0.01 ms/step — 3 gap(s)/step totalling 0.01 ms where the next kernel (aten::_to_copy) had been submitted long before the GPU went idle: the compute stream was waiting on an event from another stream

Top kernels by GPU time (roof fraction vs this GPU's BF16 peak / DRAM bandwidth; occupancy not captured):

| Op | Count | Total (ms) | Share | Bound | % of roof |
|---|---|---|---|---|---|
| aten::mm | 30 | 34.76 | 44.4 % | compute | 78 % |
| aten::addmm | 16 | 18.69 | 23.9 % | compute | 77 % |
| aten::_fused_adamw_ | 2 | 12.25 | 15.6 % | memory | 34 % |
| aten::_to_copy | 70 | 3.79 | 4.8 % | memory | 99 % |
| aten::gelu_backward | 8 | 3.58 | 4.6 % | memory | 88 % |
| aten::gelu | 8 | 2.11 | 2.7 % | memory | 99 % |

Device file: NVIDIA GeForce RTX 4060 Laptop GPU, CC 8.9, 24 SMs, BF16 peak 38.2 TFLOP/s, DRAM 256 GB/s, PCIe 15.75 GB/s per direction `[MODELED from VENDOR-SPEC]`. The manuscript's worked example is an H100-class GPU (132 SMs, 989 TFLOP/s, 3.35 TB/s, Gen5 x16): **this is a laptop Ada GPU, not an H100**, so the absolute times differ; the pathologies and their signatures in the timeline are the same.

## What to conclude

- The baseline's gaps are named by their causes: the pageable copy blocks the host and cannot overlap, every `.item()` drains the queue (host_sync gaps), and the per-parameter optimizer issues bursts of tiny kernels that the GPU retires faster than the CPU can launch them (launch_bound gaps).
- The fixes remove the first two findings outright and shrink the third; the uninstrumented step-time ratio is the number to report, not the traced one (the tracer itself costs host time per op).
- `GPU busy` is not efficiency (Section 4.9): read it next to the roof fractions of the top kernels.
- A roof fraction above 100 % (for example GELU on a 16 MiB activation) is not a measurement error in the time: the working set fits in this GPU's 32 MiB L2, so the bytes never reached DRAM (exercise 6.3's mechanism). Only kernels larger than 2x L2 are held to the DRAM bound in check().
- Small STREAM_DEPENDENCY gaps (tens of µs) show up in both variants; part of each is the tracer's own event-record commands on the stream, so they are reported but not acted on.

## Not runnable on this host (probed, not faked)

| Part | Probe | Needs | Used instead |
|---|---|---|---|
| GPU activity in torch.profiler / nsys (CUPTI kernel and memcpy records: launch config, registers, shared memory) | torch.profiler with ProfilerActivity.CUDA over one step: 0 device events (232 cudaLaunchKernel calls recorded on the CPU side) | CUPTI activity tracing (native Linux driver; not delivered under WSL2 here), Nsight Compute for counters | CUDA-event tracer per aten op; occupancy / LOW_OCCUPANCY not evaluated |

- Step time = median of >= 5 uninstrumented steps (CUDA events) after warm-up; the traced captures are separate.
- 3 captures of 2 steps per variant; analyze() runs on each and the spread is reported.
- Tracer overhead (~10-30 us host time per op) inflates launch-bound gaps; FLOPs/bytes per op are [MODELED].
- Pageable vs pinned and the per-layer .item() are deliberate pathologies of the baseline step.
