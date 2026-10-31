# Lab 12 L2: NCCL bring-up, per-call floor and reduction-kernel bandwidth on one GPU

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:44:18Z.

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
**Invariants:** all passed

## Not runnable on this host

| Part | Why | Needs |
|---|---|---|
| L2: all_reduce_perf -g 8 sweep, plateau busbw, 8 B latency over 5 launches | 2+ GPUs in one host (found 1); NVLink/NVSwitch between GPUs (nvidia-smi nvlink -s shows no active links); RDMA NICs for the L3 multi-node runs (/sys/class/infiniband is empty or absent); nccl-tests all_reduce_perf built against this CUDA/NCCL (not in the image) | 1 x 8-GPU host with NVLink, nccl-tests |
| L3: multi-node rail-pinned all_reduce_perf, ib_write_bw per rail | single host, no RDMA NIC | 2+ HX8-class nodes, RoCEv2/InfiniBand NICs, MPI or Slurm |

Probe: `torch.cuda.device_count()` = 1, NVLink active = False, /sys/class/infiniband = none.

## NCCL bring-up, world_size 1

init_process_group + first all_reduce: p50 **39.5 ms**, p95 378.6 ms; NCCL 2.21.5.

## Per-call floor and reduction kernel (median per call)

| Size (B) | world-1 all_reduce (us) | a+b kernel (us) | a+b p95 (us) | a+b algbw (GB/s) | a+b DRAM traffic (GB/s) |
|---|---|---|---|---|---|
| 8 | 16.84 | 15.63 | 20.06 | 0.00 | 0.0 |
| 32 | 18.14 | 14.97 | 22.90 | 0.00 | 0.0 |
| 128 | 17.76 | 17.55 | 23.13 | 0.01 | 0.0 |
| 512 | 16.00 | 16.38 | 29.43 | 0.03 | 0.1 |
| 2048 | 15.53 | 14.71 | 56.96 | 0.14 | 0.4 |
| 8192 | 16.35 | 16.45 | 30.33 | 0.50 | 1.5 |
| 32768 | 15.65 | 15.29 | 22.25 | 2.14 | 6.4 |
| 131072 | 16.24 | 16.67 | 38.19 | 7.86 | 23.6 |
| 524288 | 15.51 | 12.71 | 23.75 | 41.26 | 123.8 |
| 2097152 | 17.46 | 15.47 | 20.71 | 135.54 | 406.6 |
| 8388608 | 18.86 | 16.19 | 22.14 | 518.07 | 1554.2 |
| 33554432 | 70.84 | 435.62 | 473.60 | 77.03 | 231.1 |
| 134217728 | 44.03 | 1689.15 | 1715.20 | 79.46 | 238.4 |
| 536870912 | 4.10 | 6792.21 | 6838.98 | 79.04 | 237.1 |

## alpha-beta fits (`fit_alpha_beta`, weighted by 1/t)

| Series | alpha (us) | B (GB/s) | Note |
|---|---|---|---|
| nccl world-1 all_reduce | 17.19 | - | software + launch floor; no data moves |
| a+b reduction kernel | 14.57 | 1070.5 | n_half = 15603 kB |
| gloo 2-rank loopback all_reduce | 401.5 | 1.95 | CPU + TCP; not comparable with NCCL |
| lab c1: 8 x H100 NVLink (SIMULATED) | 14.1 | 448 | the lab's synthetic log, same fit |

DRAM peak `[VENDOR-SPEC]`: **256 GB/s** (8001 MHz x 2 (DDR) x 128-bit bus (RTX 4060 Laptop, NVIDIA spec)); L2 cache 32 MiB. The a+b kernel reached 237 GB/s of traffic (93 % of peak) at the largest size; points below ~4 x L2 can exceed DRAM rate because they hit in cache.

## What to conclude

- alpha has a floor you can measure on one GPU: the world-1 call cost is pure software/launch. The lab's 8-GPU alpha (tens of us) is that floor plus link latency times the algorithm's step count (Section 12.3).
- The reduction kernel is a + b over 3 S bytes of memory traffic, so its rate is ~DRAM/3. On an H100 (3.35 TB/s HBM) that is ~1.1 TB/s, far above NVLink busbw (~360-480 GB/s): reductions do not limit NVLink all-reduce there. On this laptop GPU the same ratio holds against PCIe (~15.75 GB/s).
- Below n_half the fixed cost dominates: bucket small gradients (DDP's 25 MB buckets) to stay on the bandwidth side of the curve.

_Laptop Ada GPU (RTX 4060 class, 128-bit GDDR6), not H100: compare shapes and ratios, not absolute numbers. No multi-GPU collective was measured._

- alpha-beta fits use the lab's fit_alpha_beta (solutions/lab/nccl_analysis.py): t = alpha + factor*S/B, least squares weighted by 1/t. World-size-1 and the a+b kernel use factor 1 (no bus correction applies).
- Tables and fits report medians. The physical invariants (monotonicity, DRAM bound, fit quality) use the best-of-n sample per size, the uncontended cost, so that GPU time-slicing with another process cannot fail or pass them by accident.
- Small sizes run many calls per timed sample (calls_per_sample) so the sample is >> timer resolution; times are medians of >= 5 samples after 3 warm-ups.
- Not runnable on this host: L2: all_reduce_perf -g 8 sweep, plateau busbw, 8 B latency over 5 launches; L3: multi-node rail-pinned all_reduce_perf, ib_write_bw per rail. Needs: 2+ GPUs in one host (found 1); NVLink/NVSwitch between GPUs (nvidia-smi nvlink -s shows no active links); RDMA NICs for the L3 multi-node runs (/sys/class/infiniband is empty or absent); nccl-tests all_reduce_perf built against this CUDA/NCCL (not in the image).
- gloo over loopback measures CPU memory copies and the TCP stack: never compare it with NCCL.
