# Lab 13 L2: host-GPU copy bandwidth and copy/compute overlap

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:45:15Z.

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

## Bandwidth sweep (median of repetitions)

| Case | Size (MiB) | GB/s | p95 time (ms) | n |
|---|---|---|---|---|
| host_copy | 0.0625 | 10.94 | 0.062 | 20 |
| host_copy | 1 | 66.46 | 0.215 | 20 |
| host_copy | 4 | 61.91 | 0.217 | 20 |
| host_copy | 16 | 90.33 | 0.372 | 20 |
| host_copy | 64 | 32.76 | 2.598 | 10 |
| host_copy | 256 | 25.17 | 10.892 | 10 |
| host_copy | 1024 | 25.15 | 51.912 | 10 |

## Copy/compute overlap

compute 28.1 ms, copy 5.4 ms, serial 35.9 ms, overlapped 30.2 ms -> 100 % of the copy hidden.

**Not runnable here:** GPU<->NIC GPUDirect RDMA locality (Table 13.5 rows 2-3, 5-8 and 11, exercise 13.11): no RDMA device under /sys/class/infiniband on this host. Needs: RDMA NIC (mlx5-class) on the GPU's PCIe switch, perftest built with CUDA, a second node.

_CPU fallback: no PCIe transfer was measured; these are host-memory copies, the staging step a pageable H2D transfer pays on a GPU host._

- Median of >= 5 timed repetitions after 3 warm-ups; CUDA events on the GPU, perf_counter on the CPU.
- PCIe ceiling = per-lane rate after encoding x maximum link generation and width from nvidia-smi (pcie.link.gen.max, pcie.link.width.max): the maximum-capability link, an upper bound; an idle link may train down.
