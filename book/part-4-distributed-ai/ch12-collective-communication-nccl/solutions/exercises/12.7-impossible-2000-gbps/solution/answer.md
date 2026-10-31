# 12.7 — 2,000 GB/s busbw for an 8-GPU all-reduce

**Sanity check first.** An HX8 node's NVLink gives ≈ 450 GB/s per direction per GPU; even with NVLS
in-switch reduction the lab's single-node plateau is 449 GB/s. 2,000 GB/s is ≈ 4.4× physically possible:
the measurement is wrong, not the hardware fast.

**Most likely bug.** NCCL collectives (and `torch.distributed.all_reduce`) are **asynchronous with
respect to the host**: the call enqueues a kernel on a CUDA stream and returns in microseconds. A timer
such as `time.perf_counter()` stopped right after the call measures the *launch*, not the execution, so
the computed time is tiny and the bandwidth absurd.

**Fix.**

1. `torch.cuda.synchronize()` before starting and before stopping the timer — or better, record CUDA
   events on the stream (`start.record(); …; end.record(); end.synchronize(); start.elapsed_time(end)`).
2. Warm up (≥ 5 iterations) so communicator setup and buffer registration are excluded.
3. Time many iterations and divide; report the median of several launches.
4. Compute busbw correctly: algbw = bytes / time (bytes = elements × element size, a common slip is
   using element count), busbw = algbw × 2(n − 1)/n = algbw × 1.75 for n = 8.

Or simply use `nccl-tests` (`all_reduce_perf`), which already does all of this (Section 12.5).

**Why this is the "most likely" bug.** It inflates results by orders of magnitude for every size,
which matches an impossible number; a bytes/elements mix-up inflates by exactly 2× or 4× (BF16/FP32),
which would give ≈ 900–1,800 GB/s — check it second.
