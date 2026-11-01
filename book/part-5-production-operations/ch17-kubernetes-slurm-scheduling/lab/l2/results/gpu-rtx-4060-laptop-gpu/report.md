# Lab 17 L2: the GPU as a schedulable resource (discovery, diagnoser, time-slicing cost)

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T01:03:21Z.

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

## Discovery: what a device plugin would see

| Field | Value |
|---|---|
| Physical GPUs (nvidia-smi -L) | 1 |
| UUID | `GPU-fe211e06-dfa3-0d80-fb58-b775a89cc629` |
| Memory | 8188 MiB |
| Compute capability | 8.9 |
| MIG mode | [N/A] |
| Compute mode | Default |
| Device nodes | /dev/dxg |
| Would advertise | `nvidia.com/gpu: 1` |
| label `nvidia.com/gpu.product` | `NVIDIA-GeForce-RTX-4060-Laptop-GPU` |
| label `nvidia.com/gpu.count` | `1` |
| label `nvidia.com/gpu.memory` | `8188` |
| label `nvidia.com/gpu.compute.major` | `8` |
| label `nvidia.com/gpu.compute.minor` | `9` |
| label `nvidia.com/mig.capable` | `false` |
| Slurm gres.conf | `NodeName=<this-node> Name=gpu Type=geforce-rtx-4060-laptop-gpu File=/dev/nvidia0` (device file ABSENT here) |

Scheduler components present: none.

## The lab's diagnoser on this node

| Node state | Job | Physical GPUs | Allocatable | Diagnosis |
|---|---|---|---|---|
| as found (no device plugin running) | 1 GPU | 1 | 0 | DEVICE_PLUGIN_NOT_ADVERTISING |
| with a device plugin advertising | 1 GPU | 1 | 1 | NONE_FOUND |
| with a device plugin advertising | 2 GPUs | 1 | 1 | NONE_FOUND |
| with a device plugin advertising | 1 GPU, selector H100 | 1 | 1 | SELECTOR_MISMATCH |

The 2-GPU job on a 1-GPU node comes back NONE_FOUND: the diagnoser explains pending-*despite*-free-GPUs cases, and this one is plain insufficient capacity (Kubernetes: `Insufficient nvidia.com/gpu`).

## Sharing one GPU between two jobs `[MEASURED]`

| Measurement | Median TFLOP/s | Min | Max | n |
|---|---|---|---|---|
| job alone | 27.530 | 27.486 | 27.623 | 8 |
| job A, shared | 10.772 | 10.744 | 10.906 | 8 |
| job B, shared | 10.802 | 10.749 | 10.955 | 8 |
| A + B, shared | 21.560 | 21.503 | 21.791 | 8 |

Slowdown per job **2.56x**; aggregate **0.78x** of one job alone; split A:B 1.00.
When job B allocated 1 GiB, job A's free memory (cudaMemGetInfo) dropped by **0.00 GiB** (6.87 -> 6.87 GiB of 8.00); nvidia-smi memory.used went 302.0 -> 1326.0 MiB.

What to conclude:

- A GPU that is not advertised does not exist to the scheduler: with the hardware present and no device plugin, the diagnoser says DEVICE_PLUGIN_NOT_ADVERTISING, the same evidence as an allocatable of 0 on a real node.
- Two jobs on one device under time-slicing each ran 2.56x slower and together did 0.78x the work of one job alone: sharing buys nothing for throughput-bound jobs, stretches each one's step time by more than 2x, because context switching costs extra, and is invisible to the scheduler. The device-wide view (nvidia-smi) shows job B's allocation (1.00 GiB more in use), but job A's own free-memory query did not move: under WSL2 the Windows (WDDM) driver virtualises and pages GPU memory per process, so a job cannot see its neighbour coming. On bare-metal Linux the drop is visible in both views; either way nothing stops one job pushing the other out of memory. That is why `nvidia.com/gpu` is an integer resource, and why sharing is an explicit choice (time-slicing replicas, MPS, or MIG on parts that support it; this one reports MIG not supported).
- Labels come from the hardware: a job pinned to an H100 product label will never land here, and the diagnoser says why (SELECTOR_MISMATCH).
- This is one laptop host, not an 8-GPU HX8 node: socket-aware placement, rails and gang scheduling need the L3 multi-node setup.

## Not runnable on this host

- **kind/k3s + GPU Operator (or single-node Slurm with gres/gpu): allocatable snapshot, taint/quota/selector events reproduced on a lab node**: needs a Linux GPU host where you can run a kubelet or slurmd (root), the NVIDIA device plugin / GPU Operator, /dev/nvidia* device nodes (WSL2 exposes /dev/dxg), network for the control plane.
- **L3: 2-node all_reduce_perf under two placements, gang time-to-start**: needs >= 2 multi-GPU nodes with RDMA NICs, Slurm or Kubernetes with gang scheduling.

- Sharing test: two independent worker processes, each a GEMM loop (2048^3, FP16 on the GPU), 2.0 s per measurement; solo and shared measurements interleaved, 8 repetitions each; after 5 warm-up GEMMs.
- Labels follow GPU Feature Discovery's naming (nvidia.com/gpu.product = the product name with spaces as '-').
