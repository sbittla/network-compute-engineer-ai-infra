# 4.9 — Launch-bound loop and copy cost (model answer)

Relies on manuscript Section 4.5 ("What a launch costs", "Reducing launch overhead") and Section 4.6
(pinned vs pageable). All results `[MODELED]`; `solve.py` asserts each one.

## (a) Eager mode

The CPU needs 10 µs per launch but each kernel takes only 6 µs on the GPU, so the GPU drains its queue faster
than the CPU fills it: the loop is **CPU-limited**.

- Iteration = 400 × 10 µs = **4.0 ms** (plus the last kernel's 6 µs tail, negligible).
- Kernel-busy = 400 × 6 µs / 4,000 µs = 2.4 / 4.0 = **60 %**; the GPU is idle 40 % of the time.

## (b) One CUDA Graph

One replay call costs ≈ 15 µs of CPU; the GPU then runs the kernels back to back with ≈ 1 µs between them, so
the loop becomes **GPU-limited**.

- Iteration = 15 + 400 × 6 + 399 × 1 = 2,400 + 399 + 15 = **2,814 µs ≈ 2.81 ms**.
- Speedup = 4.0 / 2.81 = **1.42×**; kernel-busy = 2.4 / 2.81 = **85 %**.

## (c) The 256 MiB input

256 MiB = 268,435,456 B.

- Pageable at 12 GB/s: 268,435,456 / 12 × 10⁹ = **22.4 ms**, serial and host-blocking. Eager iteration
  ≈ 22.4 + 4.0 = **26.4 ms**; the copy, not the kernels, dominates.
- Pinned at 50 GB/s: 268,435,456 / 50 × 10⁹ = **5.37 ms**.
- Prefetching the pinned copy on a side stream during the previous iteration hides it only if compute per
  iteration ≥ copy time. With graphs, compute is 2.81 ms < 5.37 ms, so the steady-state iteration is
  max(2.81, 5.37) = **5.37 ms: copy-bound**.

**The honest conclusion.** PCIe, not the GPU, sets throughput once graphs fix the launch problem. Deeper
prefetching does not help (the link is bandwidth-bound, not latency-bound). Reduce the bytes per iteration:
keep data resident in HBM, send token IDs rather than dense tensors, or compress.

**Common wrong answers.** Adding 4.0 ms and 2.4 ms in (a) (CPU and GPU overlap); reporting the pinned case as
2.81 ms "because the copy is hidden" (full marks require noticing the copy-bound steady state); using
256 × 10⁶ B instead of 256 MiB (gives 21.3 ms and 5.12 ms).
