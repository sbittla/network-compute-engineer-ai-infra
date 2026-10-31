# Lab 12 L2: NCCL bring-up, per-call floor and reduction-kernel bandwidth on one GPU

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:44:33Z.

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

## Not runnable on this host

| Part | Why | Needs |
|---|---|---|
| L2: all_reduce_perf -g 8 sweep, plateau busbw, 8 B latency over 5 launches | 2+ GPUs in one host (found 0); NVLink/NVSwitch between GPUs (nvidia-smi nvlink -s shows no active links); RDMA NICs for the L3 multi-node runs (/sys/class/infiniband is empty or absent); nccl-tests all_reduce_perf built against this CUDA/NCCL (not in the image) | 1 x 8-GPU host with NVLink, nccl-tests |
| L3: multi-node rail-pinned all_reduce_perf, ib_write_bw per rail | single host, no RDMA NIC | 2+ HX8-class nodes, RoCEv2/InfiniBand NICs, MPI or Slurm |

Probe: `torch.cuda.device_count()` = 0, NVLink active = False, /sys/class/infiniband = none.

## GLOO bring-up, world_size 1

init_process_group + first all_reduce: p50 **1.0 ms**, p95 5.2 ms.

## Per-call floor and reduction kernel (median per call)

| Size (B) | world-1 all_reduce (us) | a+b kernel (us) | a+b p95 (us) | a+b algbw (GB/s) | a+b DRAM traffic (GB/s) |
|---|---|---|---|---|---|
| 8 | 87.18 | 0.87 | 1.06 | 0.01 | 0.0 |
| 32 | 72.96 | 0.84 | 1.27 | 0.04 | 0.1 |
| 128 | 66.48 | 0.87 | 1.11 | 0.15 | 0.4 |
| 512 | 65.11 | 0.89 | 1.06 | 0.57 | 1.7 |
| 2048 | 68.78 | 1.25 | 2.73 | 1.64 | 4.9 |
| 8192 | 72.38 | 2.02 | 2.89 | 4.06 | 12.2 |
| 32768 | 62.80 | 2.56 | 4.37 | 12.80 | 38.4 |
| 131072 | 71.44 | 5.32 | 8.41 | 24.65 | 73.9 |
| 524288 | 64.83 | 10.12 | 24.27 | 51.81 | 155.4 |
| 2097152 | 73.35 | 23.44 | 30.53 | 89.48 | 268.4 |
| 8388608 | 159.68 | 141.38 | 173.39 | 59.33 | 178.0 |
| 33554432 | 166.97 | 1980.84 | 2395.41 | 16.94 | 50.8 |
| 134217728 | 124.04 | 8823.59 | 9373.52 | 15.21 | 45.6 |
| 536870912 | 173.70 | 36340.63 | 39825.80 | 14.77 | 44.3 |

## alpha-beta fits (`fit_alpha_beta`, weighted by 1/t)

| Series | alpha (us) | B (GB/s) | Note |
|---|---|---|---|
| gloo world-1 all_reduce | 72.93 | - | software + launch floor; no data moves |
| a+b reduction kernel | 0.97 | 58.5 | n_half = 57 kB |
| gloo 2-rank loopback all_reduce | 430.4 | 1.72 | CPU + TCP; not comparable with NCCL |
| lab c1: 8 x H100 NVLink (SIMULATED) | 14.1 | 448 | the lab's synthetic log, same fit |

## What to conclude

- alpha has a floor you can measure on one GPU: the world-1 call cost is pure software/launch. The lab's 8-GPU alpha (tens of us) is that floor plus link latency times the algorithm's step count (Section 12.3).
- The reduction kernel is a + b over 3 S bytes of memory traffic, so its rate is ~DRAM/3. On an H100 (3.35 TB/s HBM) that is ~1.1 TB/s, far above NVLink busbw (~360-480 GB/s): reductions do not limit NVLink all-reduce there. On this laptop GPU the same ratio holds against PCIe (~15.75 GB/s).
- Below n_half the fixed cost dominates: bucket small gradients (DDP's 25 MB buckets) to stay on the bandwidth side of the curve.

_CPU fallback: gloo replaced NCCL and host memory replaced GPU DRAM. GPU-only invariants (DRAM bound, NCCL version, alpha plausibility) were skipped._

- alpha-beta fits use the lab's fit_alpha_beta (solutions/lab/nccl_analysis.py): t = alpha + factor*S/B, least squares weighted by 1/t. World-size-1 and the a+b kernel use factor 1 (no bus correction applies).
- Tables and fits report medians. The physical invariants (monotonicity, DRAM bound, fit quality) use the best-of-n sample per size, the uncontended cost, so that GPU time-slicing with another process cannot fail or pass them by accident.
- Small sizes run many calls per timed sample (calls_per_sample) so the sample is >> timer resolution; times are medians of >= 5 samples after 3 warm-ups.
- Not runnable on this host: L2: all_reduce_perf -g 8 sweep, plateau busbw, 8 B latency over 5 launches; L3: multi-node rail-pinned all_reduce_perf, ib_write_bw per rail. Needs: 2+ GPUs in one host (found 0); NVLink/NVSwitch between GPUs (nvidia-smi nvlink -s shows no active links); RDMA NICs for the L3 multi-node runs (/sys/class/infiniband is empty or absent); nccl-tests all_reduce_perf built against this CUDA/NCCL (not in the image).
- gloo over loopback measures CPU memory copies and the TCP stack: never compare it with NCCL.
- CPU fallback: the floor sweep uses gloo (world_size 1) and the reduction kernel runs on host memory; no GPU, NCCL or DRAM-bound invariant applies.
