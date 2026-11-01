# Lab 4 L2: capture, classify and analyse a real training step (before and after the fixes)

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:53:44Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

## Workload

MLP of 4 blocks (d = 256, 4d hidden), 2.1 M parameters, 512 tokens per step, FP32, AdamW. **Baseline**: pageable batch copy, a `.item()` debug hook on every Linear, per-parameter (for-loop) AdamW. **Fixed**: pinned batch prefetched one step ahead with `non_blocking=True`, no hook, fused AdamW (foreach on the CPU).

## Step time, uninstrumented (Chapter 6 protocol)

| Variant | n | Median (ms) | p95 (ms) | IQR (ms) | min-max (ms) | Optimizer step alone, median (p95) ms | Kernel launches / step | Host syncs / step |
|---|---|---|---|---|---|---|---|---|
| baseline | 10 | 121.31 | 248.00 | 71.25 | 69.10-248.00 | 4.728 (11.247) | 0 | 0 |
| fixed | 10 | 45.40 | 71.71 | 23.67 | 40.75-71.71 | 4.141 (6.110) | 0 | 0 |

Whole-step ratio on the CPU: 2.67x. The GEMMs dominate a CPU step and the device-side fixes have nothing to fix (no H2D copy, `.item()` waits for no device), so this ratio is noise around 1; the optimizer step alone shows why: the foreach AdamW cuts aten dispatches per step (664 -> 587), but on a CPU the update of million-element weights is memory-bound, not dispatch-bound, so it need not be faster. On a GPU each dispatch is a kernel launch, and the same change removes launch-bound gaps.

## CPU capture: aten self time by category (baseline vs fixed, torch.profiler)

| Category | Baseline (us) | Fixed (us) |
|---|---|---|
| gemm | 41469 | 42194 |
| elementwise | 13946 | 16948 |
| cast/copy | 1862 | 1604 |
| reduction | 1401 | 1123 |
| sync | 53 | 13 |
| optimizer | 0 | 1240 |

Lab `analyze()` on the shipped SIMULATED ORION trace: findings EXCESS_SYNC, LAUNCH_BOUND, LOW_OCCUPANCY, PAGEABLE_H2D, STREAM_DEPENDENCY; gaps by cause {'launch_bound': 1200, 'host_sync': 30, 'dependency': 2}.

_CPU fallback: no GPU was used. There is no GPU timeline, no PCIe copy and no device to sync with, so the trace-schema export, the gap attribution on real data and the GPU-only invariants (PCIe and roof bounds, sync and pageable findings) were skipped._

- CPU fallback: torch limited to 4 threads; step time = median of >= 5 steps (perf_counter).
- The shipped trace is the lab's SIMULATED ORION capture; it is analysed here only to exercise the pipeline in the GPU image.
