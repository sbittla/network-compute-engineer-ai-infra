# Lab 13 L2: host-GPU copy bandwidth and copy/compute overlap

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:44:51Z.

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

## Bandwidth sweep (median of repetitions)

| Case | Size (MiB) | GB/s | p95 time (ms) | n |
|---|---|---|---|---|
| h2d_pageable | 0.0625 | 0.57 | 0.211 | 20 |
| h2d_pinned | 0.0625 | 2.35 | 0.054 | 20 |
| d2h_pinned | 0.0625 | 1.70 | 0.209 | 20 |
| h2d_pageable | 1 | 4.10 | 0.464 | 20 |
| h2d_pinned | 1 | 9.53 | 0.139 | 20 |
| d2h_pinned | 1 | 9.62 | 0.118 | 20 |
| h2d_pageable | 4 | 7.61 | 0.762 | 20 |
| h2d_pinned | 4 | 11.14 | 0.403 | 20 |
| d2h_pinned | 4 | 9.12 | 0.556 | 20 |
| h2d_pageable | 16 | 9.72 | 1.845 | 20 |
| h2d_pinned | 16 | 10.90 | 1.749 | 20 |
| d2h_pinned | 16 | 10.01 | 1.721 | 20 |
| h2d_pageable | 64 | 9.95 | 6.907 | 10 |
| h2d_pinned | 64 | 12.23 | 6.124 | 10 |
| d2h_pinned | 64 | 13.14 | 5.158 | 10 |
| h2d_pageable | 256 | 10.03 | 28.289 | 10 |
| h2d_pinned | 256 | 12.87 | 20.904 | 10 |
| d2h_pinned | 256 | 13.09 | 20.984 | 10 |
| h2d_pageable | 1024 | 9.17 | 181.081 | 10 |
| h2d_pinned | 1024 | 12.71 | 85.936 | 10 |
| d2h_pinned | 1024 | 12.99 | 84.693 | 10 |

PCIe ceiling from the maximum-capability link: **15.8 GB/s** per direction `[MODELED]`.

## Copy/compute overlap

compute 156.7 ms, copy 21.7 ms, serial 174.0 ms, overlapped 159.5 ms -> 67 % of the copy hidden.

**Not runnable here:** GPU<->NIC GPUDirect RDMA locality (Table 13.5 rows 2-3, 5-8 and 11, exercise 13.11): no RDMA device under /sys/class/infiniband on this host. Needs: RDMA NIC (mlx5-class) on the GPU's PCIe switch, perftest built with CUDA, a second node.

- Median of >= 5 timed repetitions after 3 warm-ups; CUDA events on the GPU, perf_counter on the CPU.
- PCIe ceiling = per-lane rate after encoding x maximum link generation and width from nvidia-smi (pcie.link.gen.max, pcie.link.width.max): the maximum-capability link, an upper bound; an idle link may train down.
