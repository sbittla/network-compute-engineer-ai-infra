# 4.3 — Implicit host–device synchronization in PyTorch (model answer)

Relies on manuscript Section 4.6 ("Explicit and implicit synchronization", Table 4.2a). Any four of the
following, each with its mechanism, earn full marks.

| # | Pattern | Mechanism |
|---|---|---|
| 1 | `loss.item()`, `float(t)`, `t.tolist()`, `t.cpu()`, `print(t)` | The value lives in device memory; PyTorch enqueues a D2H copy and the CPU must wait until every earlier kernel on the stream has finished and the copy has landed. |
| 2 | Python control flow on a tensor, e.g. `if (t > 0).any():` | The Python interpreter needs a host `bool` to choose a branch, which forces pattern 1 underneath. |
| 3 | Data-dependent output shapes: `x[mask]`, `torch.nonzero(t)`, `torch.unique(t)`, `masked_select` | The output size depends on GPU-computed values; the CPU must learn the size to allocate the result tensor before it can launch anything that uses it. |
| 4 | Copies from/to pageable memory: `torch.tensor(list, device="cuda")`, `.cuda()` of a non-pinned tensor | The driver stages through a pinned bounce buffer with a CPU memcpy; the call blocks the host until staging (or, for D2H, the copy) completes. |
| 5 | `torch.cuda.synchronize()`, `torch.cuda.empty_cache()` | The first is an explicit device-wide wait; the second releases cached blocks with `cudaFree`, which can synchronize the device. |

**How to find them.** `torch.cuda.set_sync_debug_mode("warn")` prints a stack trace at each synchronizing
operation (development runs only). In an nsys timeline they appear as `cudaStreamSynchronize` or long
`cudaMemcpyAsync` API calls followed by a GPU idle gap.

**Common wrong answers.** Listing `torch.cuda.Event.record()` or `non_blocking=True` copies from pinned
memory: neither blocks the host. Naming the pattern without the mechanism earns no credit.
