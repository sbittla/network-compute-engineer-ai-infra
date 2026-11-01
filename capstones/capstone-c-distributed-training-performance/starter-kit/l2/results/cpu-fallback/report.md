# Capstone C L2: the benchmark harness on one GPU, profiled, with NCCL transport evidence

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:13:03Z.

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

## Ported harness (per-rank matmul + ring all-reduce, simulated ranks on one device)

4 ranks, matmul 1024x1024 fp32 (TF32 off), gradient buffer 8 MiB per rank, 3 warm-up + 20 timed steps. Statistics from `instructor/reference/harness.py`.

| Phase | median (ms) | p95 (ms) | p99 (ms) | IQR (ms) | CV |
|---|---|---|---|---|---|
| step | 32.682 | 37.642 | 37.738 | 2.196 | 0.070 |
| compute (matmuls) | 28.038 | 32.873 | 33.604 | 2.507 | 0.087 |
| ring all-reduce | 4.400 | 5.801 | 8.028 | 0.999 | 0.236 |

Compute **0.31 TFLOP/s**; ring phase moves device memory at **51 GB/s**; communication is 14 % of the step (nothing overlaps here: one stream, phases in series).

L1 cross-check (`instructor/reference/harness.py` `ring_allreduce`, 1,001 float64 elements, 4 ranks): max |difference| 0.0e+00, per-rank bytes sent identical: **True** [12016, 12016, 12008, 12008].

## Profile (CPU operator self time (torch.profiler), 3 steps; in place of an nsys capture)

| Category | time (ms) | share |
|---|---|---|
| gemm | 80.89 | 88 % |
| reduce_add | 3.23 | 4 % |
| copy | 7.49 | 8 % |
| other | 0.21 | 0 % |

## torch.distributed, world size 1 (gloo)

all_reduce of 4 MiB, 5 timed calls: median 0.123 ms.

## Not runnable here

- **multi-GPU NCCL collectives and weak scaling (8 GPUs per node, then 2+ nodes)**. Probe: torch.cuda.device_count()=0. Needs: 8-GPU node with NVLink/NVSwitch, 2+ nodes with RDMA NICs. Fallback: simulated ranks on one device; one-rank process group for the NCCL log.
- **GPUDirect RDMA / IB transport (NCCL 'Using network IB', '/GDRDMA')**. Probe: /sys/class/infiniband=none, /dev/infiniband=False. Needs: RDMA NIC (RoCEv2 or InfiniBand), nvidia_peermem or dma-buf, rdma devices passed into the container. Fallback: the NCCL log of this host parsed with nccl_transport(): it shows the Socket fallback.
- **Nsight Systems capture (nsys profile)**. Probe: nsys on PATH=False. Needs: Nsight Systems CLI in the image. Fallback: torch.profiler kernel classification.

## What to conclude

- The harness's numerics and byte accounting are identical to the L1 version. Only the device changed, so its timings can be trusted to mean what the L1 harness's meant.
- The ring phase here is bounded by device memory bandwidth, not by any link. On a real node the same phase is bounded by NVLink (intra-node) or the NIC (inter-node), and NCCL overlaps it with backward compute. This proxy runs the phases in series, so the whole ring time is exposed.
- _CPU fallback: no GPU was used. The FP32/memory-peak bounds and the NCCL transport check were skipped, and gloo replaced NCCL._

- Harness: 3 warm-up steps, then timed steps; phases timed separately with CUDA events (GPU) or perf_counter (CPU).
- Ranks are simulated on one device: the 'communication' phase is device-memory traffic, not NVLink or network. It is the L1 algorithm, ported, not a measurement of any interconnect.
- TF32 disabled so the GEMM is comparable with the FP32 CUDA-core peak.
