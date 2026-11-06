# 4.6 — NVTX `forward` 2.3 ms vs 19.6 ms of GPU kernels (model answer)

Relies on manuscript Section 4.10 ("Nsight Systems: the timeline") and Section 4.5 ("Asynchrony and the
queue"). Numbers are from the Lab 4 capture `[SIMULATED]`.

**Why the ranges differ.** NVTX push/pop calls run on the **CPU thread**; they timestamp what the host was
doing. Inside `forward` the host only *enqueues* the 85 forward kernels: each `cudaLaunchKernel` returns
after a few microseconds, so the CPU finishes the range in 2.3 ms and moves on. The GPU then executes the
queued kernels over 19.6 ms. Nothing is wrong with either number; they describe different timelines.
Where the CPU next blocks (the `log_loss` range, whose `loss.item()` waits for the forward pass) the NVTX
range absorbs the GPU time instead: `log_loss` lasts ≈ 17.6 ms, although logging itself is trivial.

**How correlation IDs resolve it.** Every CUDA API call gets a correlation ID, and every GPU activity it
produced (kernel, memcpy) carries the same ID. The join is:

1. take the API calls whose start time falls inside the NVTX range on that thread;
2. collect their correlation IDs;
3. find the GPU activities with those IDs; their min(start)–max(end) is the GPU-side extent of the range.

Nsight Systems does this join for you as "projected" NVTX ranges on the GPU row.

**Common wrong answers.**

- "The forward pass takes 2.3 ms" (reading CPU time as GPU time).
- "`log_loss` is slow, 17.6 ms" — it is the CPU waiting in `loss.item()` for forward; the actual GPU idle due
  to the loss sync is only ≈ 0.17 ms.
- Joining by timestamp overlap instead of correlation ID, which misattributes kernels from other streams.
