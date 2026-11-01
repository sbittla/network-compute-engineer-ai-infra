# Lab 17 L2: the GPU as a schedulable resource (discovery, diagnoser, time-slicing cost)

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T01:04:10Z.

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

## Discovery: what a device plugin would see

No GPU found (nvidia-smi absent or no devices). Device nodes: none.

Scheduler components present: none.

## The lab's diagnoser on this node

| Node state | Job | Physical GPUs | Allocatable | Diagnosis |
|---|---|---|---|---|
| as found (no device plugin running) | 1 GPU | 0 | 0 | NONE_FOUND |
| with a device plugin advertising | 1 GPU | 0 | 0 | NONE_FOUND |
| with a device plugin advertising | 2 GPUs | 0 | 0 | NONE_FOUND |
| with a device plugin advertising | 1 GPU, selector H100 | 0 | 0 | NONE_FOUND |

The 2-GPU job on a 1-GPU node comes back NONE_FOUND: the diagnoser explains pending-*despite*-free-GPUs cases, and this one is plain insufficient capacity (Kubernetes: `Insufficient nvidia.com/gpu`).

## Sharing one set of two CPU cores between two jobs `[MEASURED]`

| Measurement | Median TFLOP/s (CPU) | Min | Max | n |
|---|---|---|---|---|
| job alone | 0.166 | 0.155 | 0.168 | 8 |
| job A, shared | 0.067 | 0.057 | 0.076 | 8 |
| job B, shared | 0.067 | 0.057 | 0.076 | 8 |
| A + B, shared | 0.134 | 0.114 | 0.153 | 8 |

Slowdown per job **2.48x**; aggregate **0.81x** of one job alone; split A:B 1.00.

What to conclude:

- With no GPU at all the node has nothing to advertise and the diagnoser says NONE_FOUND: a pending GPU job here is plain missing capacity, not a misconfiguration.
- Two jobs on one device under time-slicing each ran 2.48x slower and together did 0.81x the work of one job alone: sharing buys nothing for throughput-bound jobs, stretches each one's step time by more than 2x, because context switching costs extra, and is invisible to the scheduler.  That is why `nvidia.com/gpu` is an integer resource, and why sharing is an explicit choice (time-slicing replicas, MPS, or MIG on parts that support it; this one reports MIG not supported).
- Labels come from the hardware: with no GPU there are none to match.
- This is one laptop host, not an 8-GPU HX8 node: socket-aware placement, rails and gang scheduling need the L3 multi-node setup.

_CPU fallback: no GPU was found, so discovery shows an empty node; the sharing test used two CPU processes on the same two cores, and the GPU-memory isolation check was skipped._

## Not runnable on this host

- **kind/k3s + GPU Operator (or single-node Slurm with gres/gpu): allocatable snapshot, taint/quota/selector events reproduced on a lab node**: needs a Linux GPU host where you can run a kubelet or slurmd (root), the NVIDIA device plugin / GPU Operator, /dev/nvidia* device nodes (WSL2 exposes /dev/dxg), network for the control plane.
- **L3: 2-node all_reduce_perf under two placements, gang time-to-start**: needs >= 2 multi-GPU nodes with RDMA NICs, Slurm or Kubernetes with gang scheduling.

- Sharing test: two independent worker processes, each a GEMM loop (768^3, FP32 on CPUs 0,1), 2.0 s per measurement; solo and shared measurements interleaved, 8 repetitions each; after 5 warm-up GEMMs.
- Labels follow GPU Feature Discovery's naming (nvidia.com/gpu.product = the product name with spaces as '-').
