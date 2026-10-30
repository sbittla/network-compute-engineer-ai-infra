# Chapter 4 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: **L1** laptop/paper ·
**L2** single GPU host · **L3** multi-node GPU + RDMA. Use Table 4.1 (H100-SXM-class) values unless an
exercise says otherwise, label every number you produce (`[MODELED]`, `[MEASURED]`, …), and show
formula → substitution → result with units.

**Chapter deliverable (course outline):** *an annotated execution trace and a short GPU performance
analysis* — produced by Exercise 4.10 (the lab) and its `analysis.md`.

---

## Knowledge checks

**4.1** ★ L1 — Define SM, warp, thread block and grid, and state which of them is the unit of
(a) placement on hardware and (b) instruction issue.
*Evidence required:* four one-sentence definitions and the two answers.

**4.2** ★ L1 — Thirty-two threads of a warp each load one 4-byte float. How many 32-byte sectors are
fetched when the addresses are (a) consecutive, (b) stride 2 elements, (c) stride 32 elements? What
fraction of fetched bytes is useful in each case?
*Evidence required:* sector counts and useful-byte fractions with arithmetic.

**4.3** ★ L1 — Name four PyTorch code patterns that cause an implicit host–device synchronization and
explain the mechanism for each.
*Evidence required:* four patterns, each with a one-line mechanism.

**4.4** ★ L1 — Explain three distinct reasons a `cudaMemcpyAsync` from pageable memory is worse than
one from pinned memory.
*Evidence required:* bandwidth, host-blocking and overlap arguments.

**4.5** ★ L1 — What exactly does nvidia-smi `utilization.gpu` measure? Give an example in which it reads
100 % while the GPU delivers less than 5 % of its peak, and name two DCGM fields that would reveal it.
*Evidence required:* definition, example with numbers, two field names with meanings.

**4.6** ★★ L1 — Nsight Systems shows an NVTX range `forward` lasting 2.3 ms, but the forward kernels
on the GPU row span 19.6 ms. Explain the discrepancy and how correlation IDs resolve it.
*Evidence required:* explanation of CPU-side ranges and the join.

**4.7** ★★ L1 — Why can a tensor-core GEMM at 18.75 % theoretical occupancy run at 60 %+ of peak, while
a layernorm backward at 12.5 % occupancy runs at 22 % of HBM bandwidth?
*Evidence required:* latency-hiding argument referencing warp groups/TMA and Little's law.

## Worked problems

**4.8** ★★ L1 — *Occupancy and bytes in flight.* A memory-bound kernel uses 128 threads per block,
80 registers per thread and 48 KB (49,152 B) of shared memory per block. Each warp keeps two independent
128-byte loads in flight.
(a) Compute theoretical occupancy and the limiter using the Section 4.7 rules.
(b) Using Little's law with 600 ns latency and 3.35 TB/s, estimate the bytes in flight needed per SM and
the fraction of HBM bandwidth this kernel can reach at that occupancy `[MODELED]`.
(c) Shared memory per block is reduced to 32 KB (32,768 B). Recompute (a) and (b).
*Evidence required:* every limit computed, limiter named, bandwidth bound with arithmetic.

**4.9** ★★ L1 — *Launch-bound loop and copy cost.* An inference loop issues 400 kernels per iteration
with an average GPU duration of 6 µs; the CPU spends 10 µs per launch (API + framework). Each iteration
also needs a 256 MiB input.
(a) Iteration time and GPU kernel-busy fraction in eager mode.
(b) Iteration time if the 400 kernels are captured in one CUDA Graph (one replay ≈ 15 µs of CPU, ≈ 1 µs
between kernels on the GPU).
(c) Copy time for the input from pageable memory at 12 GB/s versus pinned at 50 GB/s, and the
critical-path cost of each if the pinned copy is prefetched on a side stream during the previous iteration.
*Evidence required:* three results with formulas and units; label `[MODELED]`.

## Hands-on lab

**4.10** ★★ L1 (L2 extension) — Complete [Lab 4](lab/README.md): implement the trace-analysis module,
pass `python check.py`, generate `report.md`, and write `analysis.md` (annotated execution trace and
short GPU performance analysis).
*Evidence required:* checker output (all PASS), `report.md`, `analysis.md` per the lab rubric.

## Outline-mandated exercises

**4.11** ★ L1 — *Trace an operation end to end.* For a BF16 matrix multiplication C = A × B with
N = 8,192 (square) on one ORION GPU, where A and B start in pinned host memory and C must return to the
host: (a) draw the sequence of host launch, H2D copies, kernel, D2H copy and synchronization (Mermaid or
ASCII), marking where the CPU waits and where the GPU waits; (b) estimate each stage's time at 52 GB/s
PCIe and 70 % of 989 TFLOP/s `[MODELED]`; (c) propose how a real training job avoids paying (b)'s copy
costs.
*Evidence required:* annotated diagram, three stage times with arithmetic, one-paragraph restructuring.

**4.12** ★★ L1 (L2 to verify) — *Identify the bottleneck class from a trace.* Using the lab capture (or a
CUDA sample such as `bandwidthTest`/a vector-add run on an L2 host), identify one instance each of launch
overhead, memory-transfer cost, an occupancy constraint and a memory-bandwidth bottleneck, quoting the
rows or metrics that prove each.
*Evidence required:* four findings, each with quoted evidence (row IDs, durations, bytes, metric values).

**4.13** ★★ L1 — *Batch size and data layout.* (a) For a GEMM with output 8,192 × 2,048 tiled 128 × 256 on
132 SMs, compute tiles, waves and wave efficiency; repeat for output 1,024 × 2,048. (b) A tensor of shape
[8,192, 4,096] in BF16 is read along dimension 0 by adjacent threads (column access of a row-major
tensor). Explain the coalescing consequence and two ways to fix it. (c) Explain how halving the batch
changes GEMM arithmetic intensity and why nvidia-smi would not show the change.
*Evidence required:* wave arithmetic for both shapes, coalescing explanation, two fixes, intensity argument.

## Troubleshooting case

**4.14** ★★★ L1 — An inference service on one ORION GPU meets its p50 latency SLO but p99 latency
has tripled since a release. GPU-Util is 70–80 %. A 10-second nsys capture gives (abridged,
`[ILLUSTRATIVE]`):

```text
 Time (%)  Total Time (ns)  Num Calls   Avg (ns)     Name
     48.0    2,520,114,800      2,100   1,200,054    cudaFree
     21.5    1,128,744,120        420   2,687,486    cudaMalloc
     19.9    1,044,812,000    452,113       2,311    cudaLaunchKernel
      6.1      320,251,000      2,100     152,500    cudaStreamSynchronize
```

The GPU row shows a 1–4 ms idle gap after almost every request, each beginning when a `cudaFree` call
starts. The release notes include "free GPU memory between requests to reduce fragmentation".
Rank three hypotheses, name the discriminating evidence for each, identify the root cause, propose a safe
fix and a validation plan.
*Evidence required:* ranked hypotheses, evidence mapping, root cause, fix with rollout, validation with
percentiles.

## Design challenge

**4.15** ★★★ L1 — Design the input and step-overhead strategy for a job using all eight GPUs of an HX8
node (one rank per GPU): each rank consumes 100 MiB of input per step, target step time is 60 ms, the
optimizer touches 1,400 parameter tensors (1,200 of them under 64 K elements), and shapes are static.
Decide: pinned-memory strategy and total pinned budget; where loader worker processes run (NUMA, see
Chapter 3 and Figure R.1); how copies overlap compute; how to remove optimizer launch overhead (foreach,
fused, CUDA Graphs or `torch.compile`) — and defend each choice against one alternative. State how you
would prove the design works.
*Evidence required:* a one-page design with PCIe budget arithmetic, pinned-memory budget, NUMA placement,
the overhead strategy with a rejected alternative, and a validation plan.

## Reflection and review

**4.16** ★ L1 — Which numbers in the Chapter 4 worked example are `[SIMULATED]`, which `[MODELED]`, and
what would you need to make the projected 63 ms step time `[MEASURED]`?

**4.17** ★ L1 — The lab's gap classifier uses a 10 µs launch-latency allowance and a 2 µs gap threshold.
How could each choice misclassify gaps on real hardware, and how would you calibrate them?

**4.18** ★★ L1 — Name two things a single-GPU trace cannot tell you about the same job running on 256
GPUs, and which later chapters address them.

**4.19** ★ L1 — Why is "fix the most interesting finding first" a bad prioritization rule? Use the
worked example's numbers.

*Evidence required for 4.16–4.19:* short written answers (≤ 150 words each) that cite specific numbers
or mechanisms.
