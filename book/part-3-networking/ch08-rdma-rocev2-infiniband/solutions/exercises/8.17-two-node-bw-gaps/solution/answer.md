# 8.17 — What a two-node `ib_write_bw` result does not tell you (model answer)

Relies on manuscript Section 8.10 (perftest and the evidence it gives), Section 8.8 (multi-rail,
GPUDirect RDMA), Section 8.6, and Chapter 9.

A two-node `ib_write_bw` at 390 Gb/s `[MEASURED]` proves one thing: **one QP between two host-memory
buffers on one rail reaches ≈ 99.5 % of the 392 Gb/s ceiling**. Any three of these gaps earn full
marks, each with its mechanism:

1. **Congestion and incast across many senders.** Two nodes never oversubscribe a port. A 256-GPU
   all-reduce or all-to-all puts many senders on one egress, so queues build, ECN marks and DCQCN cut
   rates, PFC pauses spread upstream, and HOL blocking creates victim flows (Chapter 9). Throughput and
   tail latency under fan-in are untested.
2. **ECMP and rail collisions with many flows.** perftest runs same-rail, single-hop between two NICs,
   so ECMP is not consulted. Cross-rail traffic on the spine hashes few large flows onto 32 uplinks
   (8.5): collisions halve some flows, and a collective runs at its slowest flow.
3. **The GPUDirect RDMA path.** A host-memory test bypasses GPU↔NIC PCIe peer-to-peer. ACS/IOMMU
   settings, `nvidia_peermem` / DMA-BUF and NCCL's GDR distance gate decide whether training traffic
   goes GPU → NIC directly or is staged through host memory. Only `ib_write_bw --use_cuda` or NCCL's
   `/GDRDMA` channel lines show it (docs/VERIFIED_FACTS.md).
4. **NCCL algorithm and protocol overheads.** Ring/tree choice, channels, chunking, proxy threads and
   synchronization. Collective bus bandwidth is not link bandwidth.
5. **Stragglers and scale effects.** One slow node, NIC, PCIe link (x8, as in Lab 8) or a noisy host
   gates every synchronous step.
6. **Long-run stability.** A 10-second test misses link flaps, FEC degradation, thermal throttling,
   and the rare loss whose tail-timeout cost dominates (8.9).

**Common mistake:** listing "the job might be slower" without naming the mechanism.
