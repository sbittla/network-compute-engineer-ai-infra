# Chapter 13 hands-on: moving data to the GPU on `NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, 592.82`

Run captured 2026-11-05T02:36:16+00:00 (24 CPUs, kernel `6.18.54.1-rxe+`). Every number is `[MEASURED]` by the step named; raw outputs are in the step directories.

## Step 1: pinned versus pageable, and what pinning costs

| Size | Pageable H2D | Pinned H2D | CPU held, pageable | CPU held, pinned | `pin_memory()` first / median | Pin every batch |
|---|---|---|---|---|---|---|
| 1 MiB | 6.33 GB/s | 10.86 GB/s | 0.089 ms | 0.009 ms | 0.07 / 0.03 ms | 8.62 GB/s |
| 8 MiB | 9.08 GB/s | 12.70 GB/s | 0.793 ms | 0.015 ms | 7.83 / 0.19 ms | 9.82 GB/s |
| 64 MiB | 9.79 GB/s | 12.85 GB/s | 6.763 ms | 0.024 ms | 48.77 / 3.39 ms | 7.79 GB/s |

All cells `[MEASURED]`.

## Step 2: overlapping copies with compute

12 chunks of 64 MiB; compute per chunk calibrated to ≈ one chunk's copy (5.224 ms copy, k = 7).

| Schedule | Wall | Σ copy | Σ compute | Copy time overlapped with compute | Copy hidden |
|---|---|---|---|---|---|
| serial | 118.1 ms | 64.5 ms | 53.5 ms | 0.0 ms | 0% |
| overlap_pinned | 67.2 ms | 62.7 ms | 53.3 ms | 49.0 ms | 78% |
| overlap_pageable | 128.6 ms | 73.8 ms | 54.1 ms | 0.0 ms | 0% |

All cells `[MEASURED]` from per-operation CUDA event timestamps. Serial / overlapped (pinned) = 1.758× `[MEASURED]`; the ideal overlapped wall time is max(Σ copy, Σ compute) = 62.7 ms.
torch.profiler GPU-side events captured: 0 `[MEASURED]` (no CUPTI GPU activity on this platform, so the event timestamps are the evidence).

## Step 3: the DataLoader configuration that keeps the GPU busy

- Ceiling (batch already on the GPU): 3585.8 samples/s (17.848 ms per step) `[MEASURED]`.
- One process produces a batch in 63.34 ms (1010.4 samples/s) `[MEASURED]`; estimate ⌈63.34 / 17.848⌉ = 4 workers to keep up.

| Configuration | Samples/s | Data wait | GPU busy (events) | utilization.gpu |
|---|---|---|---|---|
| workers 0, pin off | 734 | 92% | 29% | 27.8 % |
| workers 1, pin off, prefetch 2 | 895 | 89% | 37% | 38.6 % |
| workers 2, pin off, prefetch 2 | 1623 | 66% | 45% | 40.7 % |
| workers 4, pin off, prefetch 2 | 2953 | 22% | 81% | 58 % |
| workers 8, pin off, prefetch 2 | 2928 | 11% | 81% | 61 % |
| workers 12, pin off, prefetch 2 | 2775 | 12% | 77% | 70.2 % |
| workers 0, pin on | 815 | 94% | 33% | 34.5 % |
| workers 2, pin on, prefetch 2 | 1554 | 91% | 43% | 49.7 % |
| workers 4, pin on, prefetch 2 | 3018 | 78% | 83% | 68.3 % |
| workers 8, pin on, prefetch 2 | 3419 | 40% | 94% | 76.7 % |
| workers 12, pin on, prefetch 2 | 3424 | 10% | 95% | 76.7 % |
| workers 4, pin on, prefetch 1 | 2949 | 80% | 80% | 73.8 % |
| workers 4, pin on, prefetch 4 | 3074 | 77% | 84% | 57.3 % |
| workers 4, pin on, prefetch 8 | 2923 | 79% | 80% | 68 % |

All cells `[MEASURED]`.

- Best: workers 12, pin on, prefetch 2 at 3424 samples/s, 96% of the ceiling `[MEASURED]`.
- Cheapest configuration within 5 % of the best: workers 8, pin on, prefetch 2 (3419 samples/s, GPU busy 94%) `[MEASURED]`.

