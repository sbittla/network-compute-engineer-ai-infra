# 5.12 — P2P versus host-staged transfer, GPU2 → GPU6 on HX8 (model answer)

Relies on manuscript Section 5.4 ("GPU to GPU inside a node"), Section 5.5 (NUMA) and Chapter 4 Section 4.6
(pinned vs pageable). Times `[MODELED]`; `solve.py` asserts them. GPU2 is on socket 0, GPU6 on socket 1.

## (a) Pinned or P2P

**NVLink P2P** (`cudaMemcpyPeerAsync` with peer access enabled): one DMA from GPU2 HBM through NVSwitch into GPU6
HBM; completion signalled by an event on the stream; no host memory, no CPU copy.

**Host-staged with a pinned buffer:**

1. Copy 1, D2H: GPU2 HBM → pinned host buffer (GPU2's copy engine, over PCIe).
2. Synchronization point: an event recorded after copy 1, waited on by the stream that issues copy 2 (or a
   host `cudaEventSynchronize`).
3. Copy 2, H2D: pinned buffer → GPU6 HBM (GPU6's copy engine, over PCIe).

## (b) Pageable buffers

Each leg adds a CPU memcpy between the user's pageable buffer and the driver's internal pinned bounce buffer,
and each call blocks the host thread: effectively 2 DMAs + 2 CPU copies, with implicit synchronization per
call and no overlap between the legs.

## (c) Times for 4 GiB = 4,294,967,296 B

| Path | Arithmetic | Time |
|---|---|---|
| NVLink | 4,294,967,296 / 370 × 10⁹ | **11.6 ms** |
| Host-staged, unpipelined | 2 × 4,294,967,296 / 52 × 10⁹ = 2 × 82.6 | **165.2 ms** |
| Host-staged, 64 MiB chunks | 82.6 + 67,108,864 / 52 × 10⁹ = 82.6 + 1.3 (legs overlap except for one chunk) | **83.9 ms** |

Pageable staging would be slower still (CPU copies at ≈ 10–25 GB/s). NVLink is ≈ 7× faster than the best
host-staged case.

## (d) Where should the staging buffer live?

Any choice puts one leg across the inter-socket link: on socket 0, the H2D to GPU6 reads remote memory; on
socket 1, the D2H from GPU2 writes remote memory. Options are two staging buffers (one per socket) with a
CPU-side or DMA copy between them, or splitting the buffer, each adding work. The awkwardness is the lesson:
host staging between sockets is a poor fallback; ensure P2P over NVLink works (`nvidia-smi topo -p2p r`,
`p2pBandwidthLatencyTest`).

**Common wrong answers.** Forgetting the synchronization point between the legs; pipelined time = 82.6 / 2.
