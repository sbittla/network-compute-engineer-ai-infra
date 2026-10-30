# Chapter 4 — GPU Architecture and CUDA Execution

*Part II — Accelerated Compute · Course week 3 · Progressive Lab 4 (GPU baseline), part 1*

A working model of the GPU execution machine for infrastructure engineers: streaming multiprocessors,
warps and SIMT, the memory hierarchy from registers to HBM and host memory, kernels and launch overhead,
streams, events and synchronization (including the implicit kinds), pinned versus pageable memory,
occupancy and when it matters, tensor cores, and profiling with Nsight Systems, Nsight Compute and the
PyTorch profiler. The chapter's worked example and lab decompose an 85 ms training step on an ORION
HX8 GPU into idle time, copy time and kernel inefficiency, and rank five planted problems by their cost.

## Learning objectives

1. **Explain** how a CUDA kernel launch becomes work on the GPU: grid → thread blocks → warps → SIMT
   instructions issued by SM warp schedulers, and why GPUs hide latency with parallelism rather than caches.
2. **Describe** the H100-class memory hierarchy with representative capacities and bandwidths, and
   **identify** which level a performance problem lives in.
3. **Trace** a vector-add or matrix-multiplication operation through host launch, host-to-device copy,
   kernel execution, device-to-host copy and synchronization, naming every point where the CPU or GPU waits.
4. **Calculate** theoretical occupancy from block size, registers per thread and shared memory per block,
   name the limiter, and **judge** whether low occupancy is actually a problem for a given kernel.
5. **Diagnose** launch-overhead-bound kernels, host-blocking pageable copies, unnecessary
   synchronizations and latency-starved low-occupancy kernels from a profiler trace, and **estimate**
   what each costs per step.
6. **Use** Nsight Systems, Nsight Compute and the PyTorch profiler with correct, low-risk capture options,
   and **explain** why nvidia-smi "GPU-Util" is not a measure of SM efficiency.
7. **Explain** how batch size and data layout change GPU utilization and memory behaviour.

## Prerequisites

[Chapter 3](../../part-1-foundations/ch03-linux-host-systems-diagnostics/) (Linux processes, NUMA, PCIe,
`lspci`). Python and basic C syntax. No CUDA experience required.

## Time budget

| Activity | Estimate |
|---|---|
| Reading the manuscript | 2.5–3 h |
| Exercises (knowledge checks, worked problems, case, design, reflection) | 3–4 h |
| Lab (L1) including `analysis.md` | 3–4 h |
| Optional L2 extension (single GPU host) | 2–3 h |

## Lab tiers

**L1** (required, laptop, `[SIMULATED]` capture) · **L2** extension (one GPU host: `nsys`/`ncu` capture of
your own job).

## Deliverable (course outline)

*Annotated execution trace and a short GPU performance analysis* — the lab's `report.md` plus
`analysis.md` (Exercise 4.10).

## File map

| Path | Content |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text (Sections 4.1–4.14, trade-offs, runbook, summary) |
| [exercises.md](exercises.md) | Exercises 4.1–4.19 including the outline-mandated 4.11–4.13 |
| [lab/README.md](lab/README.md) | Lab 4 guide: trace analysis of a training step |
| `lab/manifest.yaml` | Environment manifest (L1) and L2 record fields |
| `lab/data/` | Seeded `[SIMULATED]` capture: GPU trace, CUDA API trace, NVTX ranges, device limits |
| `lab/tools/generate_data.py` | Deterministic dataset generator (seed 4) — instructor copy only; removed from the student release because it encodes the planted faults |
| `lab/starter/trace_analysis.py` | Learner module (TODOs) |
| `lab/check.py` | Checker: `python check.py [--impl starter\|solution]` |
| `solutions/` | Instructor answer key and reference implementation (removed from the student release) |
| `review/REVIEW.md` | Editorial review log |

## Course placement

Week 3 — *GPU compute and interconnects* — together with
[Chapter 5](../ch05-gpu-interconnects-host-topology/) and [Chapter 6](../ch06-gpu-performance-engineering/).
Chapter 6's lab completes Progressive Lab 4 by turning this chapter's diagnosis into a repeatable baseline.
