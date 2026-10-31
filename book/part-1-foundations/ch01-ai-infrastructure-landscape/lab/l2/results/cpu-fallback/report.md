# Lab 1 L2: workload characterisation of a measured kernel mix and a GPU inventory

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:32:53Z.

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

## Platform file for this device (the lab's schema)

| Ceiling | Value | Source |
|---|---|---|
| compute (BF16 dense, here FP32 measured) | 0.31 TFLOP/s | max measured FP32 GEMM/training-step FLOP/s [MEASURED roof] |
| memory | 84.8 GB/s | max measured elementwise/GEMV bandwidth [MEASURED roof] |
| I/O and scale-up | 1.00 GB/s | no I/O path measured on the CPU fallback (placeholders; every such column is 0) |

Machine balance: **4 FLOP/B** here vs **295 FLOP/B** for the manuscript's ORION H100-class GPU (Section 1.6).

## Measured kernel mix, classified by the lab's `classify()`

| ID | Workload | Median | p95 | min-max | AI (FLOP/B) | Achieved | Lower bound | Bound (dominant) | Ceiling fraction | Flags |
|---|---|---|---|---|---|---|---|---|---|---|
| L2-TRAIN | mlp4x256-train-step (2.1 M params, 1024 tokens/step, FP32, AdamW) | 65.039 ms | 94.719 ms | 50.193 ms-98.672 ms | 96.1 | 0.20 TFLOP/s | 41.468 ms | compute (compute) | 0.64 | none |
| L2-GEMM | gemm-768 (768^3, float32) | 2.909 ms | 3.344 ms | 2.723 ms-3.612 ms | 128.0 | 0.31 TFLOP/s | 2.909 ms | compute (compute) | 1.00 | none |
| L2-DECODE | decode-gemv-b1 (weights 4096x2048 (32 MiB), batch 1) | 396.2 us | 580.1 us | 353.6 us-641.0 us | 0.5 | 84.8 GB/s | 396.2 us | memory (memory) | 1.00 | none |
| L2-ELTWISE | eltwise-add (64 MiB per tensor, FP32) | 4.611 ms | 5.345 ms | 4.306 ms-6.024 ms | 0.1 | 43.7 GB/s | 2.375 ms | memory (memory) | 0.52 | none |
| L2-TINY | tiny-launch-x200 (200 x 1024-element adds) | 904.3 us | 1.032 ms | 751.9 us-1.070 ms | 0.1 | 1.8 GB/s | 19.3 us | memory (memory) | 0.02 | LATENCY_OR_OVERHEAD |

## What to conclude

- **Decode is memory-bound here too.** The decode-gemv-b1 has an intensity of ~0.5 FLOP/B, 7x below the 4 FLOP/B balance, and runs at 85 GB/s of a 85 GB/s roof: the W02 argument of Section 1.9 holds on any GPU, because intensity ~ batch size.
- **The square GEMM and the training step are compute-bound** (ceiling fractions 1.00 and 0.64); the training step's fraction is its MFU against this device's peak, and the gap to the GEMM is optimizer, activation and launch overhead.
- **The tiny-launch burst** reaches a ceiling fraction of 0.021: no throughput ceiling explains it, which is exactly what LATENCY_OR_OVERHEAD means. Do not buy bandwidth for it; fuse or graph-capture it.

_CPU fallback: no GPU was used. The mix ran on the CPU in FP32 and was classified against the best measured CPU rates, so the GPU inventory, the vendor-ceiling bounds, the PCIe I/O row and the 25 % efficiency floor were skipped._

- Observed time = median of >= 5 timed repetitions after 3 warm-ups (CUDA events on the GPU, perf_counter on the CPU); p95, IQR and min/max are in the table. FLOP and byte counts are from shapes [MODELED]; the training-step bytes are a lower bound (optimizer state + saved activations), so its memory time is too.
- Rows are passed to the reference solution's normalize_and_validate() and classify() exactly as CSV strings.
- CPU fallback: torch limited to 4 threads; the roofs are the best measured rates, so the roof-setting rows have a ceiling fraction of 1.0 by construction.
