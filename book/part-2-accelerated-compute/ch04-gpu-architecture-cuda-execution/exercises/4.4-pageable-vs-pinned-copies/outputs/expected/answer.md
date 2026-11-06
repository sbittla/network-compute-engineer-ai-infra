# 4.4 — Pageable versus pinned `cudaMemcpyAsync` (model answer)

Relies on manuscript Section 4.6 ("Pinned versus pageable host memory", "Copy engines and bidirectional
overlap").

1. **Bandwidth.** The copy engine can only DMA from page-locked memory, so for a pageable source the driver
   first copies the data with the CPU into an internal pinned bounce buffer, chunk by chunk, then DMAs it.
   The CPU memcpy and the chunking cap throughput at typically 10–25 GB/s, against ≈ 50 GB/s for pinned
   memory on a PCIe Gen5 x16 link `[ILLUSTRATIVE]`. In the Lab 4 capture the 100,663,296-B pageable H2D copy
   runs at 12.19 GB/s while the pinned prefetch runs at ≈ 48 GB/s `[SIMULATED]`.
2. **Host blocking.** Despite the `Async` name, the call does not return until the data has been staged
   (for D2H into pageable memory, until the copy has completed). The CPU thread cannot run ahead to enqueue
   the next kernels, so the GPU queue drains and an idle gap follows (the lab's `host_sync` gaps after the
   blocking copies).
3. **No overlap.** A pageable copy serializes with the stream's work and cannot run concurrently with
   kernels the way a pinned `non_blocking=True` copy on a side stream can (copy engine and SMs working at
   the same time). The copy time therefore lands on the critical path in full.

**Consequence.** All three effects add: lower bandwidth makes the copy longer, host blocking stops the CPU
from feeding the GPU, and the lack of overlap exposes the whole copy. Fix with a reused pinned staging pool
and a side-stream prefetch one step ahead.

**Common wrong answer.** "Pinned memory is faster because it is in a faster DRAM." Pinned and pageable
pages live in the same DRAM; the difference is whether the DMA engine may access them directly.
