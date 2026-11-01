# Capstone C L2: the benchmark harness on one GPU, profiled, with NCCL transport evidence

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:12:53Z.

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

## Ported harness (per-rank matmul + ring all-reduce, simulated ranks on one device)

4 ranks, matmul 4096x4096 fp32 (TF32 off), gradient buffer 32 MiB per rank, 3 warm-up + 20 timed steps. Statistics from `instructor/reference/harness.py`.

| Phase | median (ms) | p95 (ms) | p99 (ms) | IQR (ms) | CV |
|---|---|---|---|---|---|
| step | 79.028 | 80.794 | 80.899 | 1.863 | 0.016 |
| compute (matmuls) | 74.744 | 76.631 | 76.878 | 2.277 | 0.018 |
| ring all-reduce | 4.308 | 4.395 | 4.645 | 0.433 | 0.060 |

Compute **7.36 TFLOP/s**; ring phase moves device memory at **210 GB/s**; communication is 6 % of the step (nothing overlaps here: one stream, phases in series).
Bounds: FP32 CUDA-core peak 19.1 TFLOP/s and memory 256 GB/s at max clocks `[VENDOR-SPEC]` (SMs x 128 FP32 lanes x 2 x clocks.max.sm; GDDR6 2 x clocks.max.memory x bus width).

L1 cross-check (`instructor/reference/harness.py` `ring_allreduce`, 1,001 float64 elements, 4 ranks): max |difference| 0.0e+00, per-rank bytes sent identical: **True** [12016, 12016, 12008, 12008].

## Profile (CUDA-event timed categories (CUPTI kernel trace unavailable in this container), 3 steps; in place of an nsys capture)

| Category | time (ms) | share |
|---|---|---|
| gemm | 23.60 | 65 % |
| reduce_add | 4.54 | 13 % |
| copy | 8.13 | 22 % |
| other | 0.00 | 0 % |

## torch.distributed, world size 1 (nccl)

all_reduce of 4 MiB, 5 timed calls: median 0.163 ms; NCCL 2.21.5.

| Log | network | GDR | IB devices | 'No device found' |
|---|---|---|---|---|
| this host (measured) | Socket | False | - | False |
| data/nccl_debug_baseline.log (supplied) | Socket | False | 0 | True |
| data/nccl_debug_ib_gdr.log (supplied) | IB | True | 8 | False |

Excerpt:

```text
Bootstrap : Using lo:127.0.0.1<0>
NET/Plugin: No plugin found (libnccl-net.so)
NET/Plugin: Using internal network plugin.
cudaDriverVersion 13010
Failed to open libibverbs.so[.1]
NET/Socket : Using [0]lo:127.0.0.1<0>
Could not get speed from /sys/class/net/lo/speed. Defaulting to 10 Gbps.
Using non-device net plugin version 0
Using network Socket
ncclCommInitRank comm 0x650b5de23a50 rank 0 nranks 1 cudaDev 0 nvmlDev 0 busId 1000 commId 0x3057a4c2c5f00721 - Init START
```

## Not runnable here

- **multi-GPU NCCL collectives and weak scaling (8 GPUs per node, then 2+ nodes)**. Probe: torch.cuda.device_count()=1. Needs: 8-GPU node with NVLink/NVSwitch, 2+ nodes with RDMA NICs. Fallback: simulated ranks on one device; one-rank process group for the NCCL log.
- **GPUDirect RDMA / IB transport (NCCL 'Using network IB', '/GDRDMA')**. Probe: /sys/class/infiniband=none, /dev/infiniband=False. Needs: RDMA NIC (RoCEv2 or InfiniBand), nvidia_peermem or dma-buf, rdma devices passed into the container. Fallback: the NCCL log of this host parsed with nccl_transport(): it shows the Socket fallback.
- **Nsight Systems capture (nsys profile)**. Probe: nsys on PATH=False. Needs: Nsight Systems CLI in the image. Fallback: torch.profiler kernel classification.
- **CUDA kernel trace (torch.profiler CUDA activity via CUPTI)**. Probe: torch.profiler returned no device-time records for CUDA kernels. Needs: CUPTI kernel tracing (native Linux driver; often unavailable under WSL2). Fallback: the same categories timed with CUDA events around each operation group.

## What to conclude

- The harness's numerics and byte accounting are identical to the L1 version. Only the device changed, so its timings can be trusted to mean what the L1 harness's meant.
- The ring phase here is bounded by device memory bandwidth, not by any link. On a real node the same phase is bounded by NVLink (intra-node) or the NIC (inter-node), and NCCL overlaps it with backward compute. This proxy runs the phases in series, so the whole ring time is exposed.
- The NCCL log on this host has the **same signature as the supplied baseline**: libibverbs missing, then 'Using network Socket'. Without an RDMA device in the container, NCCL silently falls back to TCP. Check this line before trusting any multi-node number.
- This is a **laptop Ada GPU, not an H100 node**. Compare shapes, never absolute numbers, with the supplied ORION logs.

- Harness: 3 warm-up steps, then timed steps; phases timed separately with CUDA events (GPU) or perf_counter (CPU).
- Ranks are simulated on one device: the 'communication' phase is device-memory traffic, not NVLink or network. It is the L1 algorithm, ported, not a measurement of any interconnect.
- TF32 disabled so the GEMM is comparable with the FP32 CUDA-core peak.
