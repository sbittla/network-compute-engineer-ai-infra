# Capstone H L2: roofline calibration of prefill and decode on one GPU

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-06T04:44:21Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-rxe+-x86_64-with-glibc2.39 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

> **Run conditions.** Swap was disabled inside the 7.8 GiB WSL2 VM for this run (`swapoff -a`, restored afterwards). It replaces the 2026-11-01 bundle, which ended with status `error`.

## Model under test

Random-weight decoder: d=2048, layers=8, heads=16, torch.float16, 403 M non-embedding parameters, 839 MB of weights, 64 KiB of KV per token.

Measured ceilings: dense GEMM **26.73 TFLOP/s** (n=4096), memory copy **225.7 GB/s** (read + write) `[MEASURED]`.
Vendor-class peaks at clocks.max.sm: FP16 tensor (FP32 accumulate) 38.2 TFLOP/s, memory 256 GB/s `[VENDOR-SPEC]` (SMs x per-SM rate x clocks.max.sm (NVIDIA Ada architecture whitepaper) [VENDOR-SPEC]).

## Prefill (output length 1)

| Prompt tokens | Median (ms) | p95 (ms) | IQR (ms) | TFLOP/s | tokens/s | L1 model (ms) | error |
|---|---|---|---|---|---|---|---|
| 64 | 4.63 | 5.27 | 0.300 | 11.15 | 13815 | 2.02 | -56 % |
| 128 | 4.97 | 5.21 | 0.115 | 20.83 | 25731 | 4.04 | -19 % |
| 256 | 8.55 | 8.79 | 0.204 | 24.35 | 29931 | 8.13 | -5 % |
| 512 | 16.28 | 16.94 | 0.228 | 25.86 | 31459 | 16.42 | +1 % |
| 1024 | 34.18 | 34.90 | 0.317 | 25.13 | 29961 | 33.51 | -2 % |
| 2048 | 69.36 | 70.28 | 0.525 | 25.76 | 29526 | 69.70 | +0 % |

## Decode step at context 512

| Batch | Median (ms) | p95 (ms) | GB/s moved | tokens/s | L1 model (ms) | error |
|---|---|---|---|---|---|---|
| 1 | 4.937 | 8.938 | 176.7 | 203 | 4.794 | -3 % |
| 2 | 4.974 | 5.601 | 182.2 | 402 | 4.967 | -0 % |
| 4 | 5.219 | 5.732 | 186.5 | 766 | 5.314 | +2 % |
| 8 | 5.952 | 6.189 | 186.1 | 1344 | 6.008 | +1 % |
| 16 | 7.358 | 7.606 | 187.1 | 2174 | 7.396 | +1 % |
| 32 | 10.212 | 10.543 | 187.5 | 3134 | 10.172 | -0 % |

## Fitted L1 constants

| Constant | L1 default (H100-class TP8) | Fitted vs measured ceiling | Fitted vs vendor peak |
|---|---|---|---|
| mfu_prefill | 0.5 | 0.96 | 0.67 |
| hbm_eff | 0.7 | 0.86 | 0.76 |
| step_overhead_s | 0.004 s | 0.29 ms | 0.29 ms |

## What-if: L1 pool sizing with the measured efficiencies `[MODELED]`

Using `instructor/reference/serve.py` `size_pools()` for the H100-class instance, swapping mfu_prefill 0.5 -> 0.67 and hbm_eff 0.7 -> 0.76:

| | P (prefill) | D (decode) | decode batch | GPUs |
|---|---|---|---|---|
| L1 defaults | 4 | 1 | 491 | 40 |
| measured efficiencies | 3 | 1 | 491 | 32 |

_This transfers efficiencies measured on a small model on a laptop GPU onto a 70B TP8 H100-class instance. Constants are relative to the vendor peak, as the L1 hardware table is. It shows how sensitive the pool sizes are to these constants; it is not a prediction for ORION._

The L1 formulas in `instructor/reference/serve.py` (`prefill_time_s`, `decode_step_time_s`, MODEL re-pointed at this model) reproduce the 'L1 model' columns to 2e-16 relative difference.

## KV transfer path available on one host

| Prompt tokens | KV bytes | Median (ms) | GB/s | path |
|---|---|---|---|---|
| 1024 | 67.1 MB | 5.118 | 13.1 | GPU->pinned host (PCIe) |
| 2048 | 134.2 MB | 10.285 | 13.0 | GPU->pinned host (PCIe) |

## Not runnable here

- **L3 KV-cache transfer between two RDMA nodes (ib_write_bw --use_cuda, GPUDirect RDMA, TCP baseline)**. Probe: /sys/class/infiniband devices=none, /dev/infiniband=True, ib_write_bw=present, torch.cuda.device_count()=1. Needs: two GPU nodes, RDMA NIC per rail (GPUDirect RDMA capable), lab switch, perftest built with CUDA. Fallback: GPU -> pinned host memory KV offload over PCIe measured instead (table kv_offload).

## What to conclude

- This is a **laptop Ada GPU (RTX 4060 class), not an H100**: absolute times are not ORION evidence. The *shape* is: prefill throughput rises with prompt length until it is compute-bound, and decode step time stays nearly flat across small batches because every step streams all the weights.
- Decode step overhead (~0.29 ms here) is mostly per-kernel launch cost from an eager Python loop; serving stacks hide it with CUDA graphs. It is the same term the L1 model calls `step_overhead_s`.
- Feed the fitted constants, not the defaults, into the capacity model, and refit on the target GPU and serving stack.

- Model: random weights, greedy argmax; output quality is irrelevant, only the cost of the work.
- Prefill FLOPs = 2*N*T + 2*L*d*T^2 and decode bytes = weights + B*ctx*KV bytes/token, the L1 formulas; l1_formula_crosscheck evaluates serve.prefill_time_s / decode_step_time_s themselves with MODEL re-pointed at this model.
- Repetitions: 3 warm-ups, >= 5 timed, interleaved round-robin across sizes; CUDA events on the GPU, perf_counter on the CPU; medians reported.
