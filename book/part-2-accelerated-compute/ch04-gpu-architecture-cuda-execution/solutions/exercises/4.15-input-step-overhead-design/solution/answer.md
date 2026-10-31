# 4.15 — Input and step-overhead strategy for one HX8 node (model answer)

Relies on manuscript Sections 4.5 (launch overhead), 4.6 (pinned memory, streams), Chapter 3 (NUMA) and
Figure R.1 / docs/REFERENCE_CLUSTER.md (HX8: 2 sockets, 2 TiB, two GPUs per PCIe Gen5 switch). Budgets
`[MODELED]`; `solve.py` asserts them. Assumption: ≈ 50 GB/s achievable pinned H2D per GPU `[ILLUSTRATIVE]`.

## 1. PCIe budget

- Per GPU: 100 MiB = 104,857,600 B per 60 ms → 104,857,600 / 0.060 = **1.75 GB/s ≈ 3.5 %** of ≈ 50 GB/s.
- Per PCIe switch uplink (two GPUs): **3.5 GB/s**, negligible against a Gen5 x16 uplink.
- Copy time per step at 50 GB/s = **2.10 ms**, 3.5 % of the step: easily hidden *if* pinned and overlapped.

PCIe is not the constraint; pageable or serialized copies would be.

## 2. Pinned memory

A reused staging pool of **3 buffers per rank** (one being filled by loaders, one in flight to the GPU, one
being consumed) = 3 × 100 MiB = **300 MiB per rank**, × 8 = **2,400 MiB ≈ 2.34 GiB per node**, 0.11 % of
2 TiB. *Rejected alternative:* `pin_memory=True` on every loader batch / pinning every tensor: unbounded
growth of page-locked memory, page-cache pressure and slow `cudaHostAlloc` calls on the hot path.

## 3. NUMA placement

Ranks 0–3 and their loader workers on socket 0 (NUMA 0), ranks 4–7 on socket 1, with staging buffers
allocated on the local node (`numactl --cpunodebind=N --membind=N`, or the launcher's affinity settings) so
DMA reads never cross the inter-socket link. Verify with `nvidia-smi topo -m` CPU/NUMA Affinity columns
(Chapter 5) and `numastat -p <pid>`. *Rejected:* letting the scheduler float workers (cross-socket DMA,
noisy step times).

## 4. Copy/compute overlap

Side-stream `non_blocking=True` copy of step *k* + 1 during step *k*; the compute stream calls
`wait_stream(copy_stream)` before use and the tensor is marked with `record_stream` so the allocator does not
reuse it early.

## 5. Optimizer launch overhead

1,400 tensors unfused ≈ 1,400 × 5 elementwise ops = 7,000 launches ≈ **70 ms** of CPU issue time at 10 µs each:
longer than the whole 60 ms step. **Choice: `fused=True` AdamW** (or `foreach=True`): one or a handful of
multi-tensor kernels, low effort, no constraints on the training loop. *Rejected alternative:* a whole-step
CUDA Graph (or `torch.compile` with `mode="reduce-overhead"`): larger potential gain, but static-address
constraints, harder debugging, and collectives inside graphs need care. Revisit only if launch gaps remain
> 2 % of the step after fusion.

## 6. Proof

nsys capture of 2 steps per rank: H2D copies on the side stream overlapping compute, pinned rate ≈ 48 GB/s,
≤ a handful of optimizer kernels; median step time over 5 runs × 300 steps (warm-up discarded) at or below
60 ms within the noise floor; DCGM `SM_ACTIVE` ≥ baseline on every GPU; `numastat` shows local allocations.

*Key note:* the key previously said "2.4 GiB per node"; 2,400 MiB is 2.34 GiB (2.52 GB). Corrected.
