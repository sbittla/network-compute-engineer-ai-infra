# 4.14 — p99 latency tripled after a release (model answer)

Relies on manuscript Section 4.6 (Table 4.3: allocator paths that synchronize), Section 4.10 (nsys) and
Section 4.14 (troubleshooting method). The capture is `[ILLUSTRATIVE]`.

## Reading the evidence

- 2,100 `cudaFree` calls in 10 s = 210 per second, one per request; 1.20 ms average, 2.52 s total (48 % of API
  time).
- 420 `cudaMalloc` calls averaging 2.69 ms: the caching allocator re-growing after being emptied.
- 2,100 `cudaStreamSynchronize` calls: the normal one per request (result read-back).
- The GPU row shows a 1–4 ms idle gap after almost every request, starting exactly when `cudaFree` starts.

## Ranked hypotheses

| Rank | Hypothesis | Discriminating evidence |
|---|---|---|
| 1 | **Allocator churn from the new "free GPU memory between requests" code** (`torch.cuda.empty_cache()` per request) | `cudaFree` count = request count; gaps aligned with `cudaFree` start; `cudaMalloc` regrowth calls; the change is in the release notes. Confirm on a canary by removing the call. |
| 2 | Genuine fragmentation causing allocation retries | `torch.cuda.memory_stats()["num_alloc_retries"]` > 0 and OOM-retry warnings *before* the release; would persist with `empty_cache` removed |
| 3 | CPU-side pauses (Python GC, logging, CPU contention) | Gaps not aligned with CUDA API calls; check with py-spy/perf and `pidstat` on the server. Ruled out by the alignment with `cudaFree`. |

## Root cause

Per-request `empty_cache()` releases the caching allocator's blocks with `cudaFree`, which **implicitly
synchronizes the device**: the CPU blocks until all queued work drains, then the GPU sits idle while the
driver frees memory. The next requests must re-grow the cache with slow `cudaMalloc` calls (2.7 ms each).
The p50 request is unaffected; the tail grows because requests queued behind a free/re-grow cycle wait for
the device to drain and the allocator to regrow (1–4 ms each time).

## Fix and rollout

1. Remove the per-request `empty_cache()`.
2. If fragmentation was the real concern, measure it first (`memory_stats`: reserved vs allocated,
   `num_alloc_retries`), then use the allocator's configuration (for example
   `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`; verify availability for the deployed PyTorch version)
   and bucketed input shapes.
3. Canary: 5 % of traffic for one hour, then staged rollout; roll back on any regression.

## Validation

- `cudaFree` call count ≈ 0 in steady state (nsys `cuda_api_sum` on the canary).
- p50/p99/p99.9 latency at matched load against the pre-release baseline; p99 within 10 % of baseline over ≥ 3
  one-hour windows.
- `num_alloc_retries` = 0 and reserved memory stable (no OOMs).

**Common wrong answers.** Blaming `cudaLaunchKernel` (largest call count, but 2.3 µs average is normal);
"add more GPUs"; removing the call without a canary or without checking fragmentation.
