# 12.5 — What a channel is, and why 16 ranks reach ≈ 350 GB/s busbw

**Channel** (Section 12.6). An NCCL channel is one independent instance of a ring (or tree): its own
ordering of ranks, its own buffers, run on each GPU by one CUDA block, and — for the hop between nodes —
its own network connection on a chosen NIC. NCCL splits each collective's buffer across all channels,
so they run in parallel. On an HX8 node NCCL builds many channels and spreads their inter-node hops
across the 8 NICs (rail-aligned: GPU i's channels leave on NIC i, Figure 12.3).

**Why 350 GB/s is not a contradiction.** busbw is the bandwidth per rank on the busiest link class,
normalized by the all-reduce factor; it is not limited by one NIC because a node's traffic leaves
through all of them in parallel:

```text
node egress     = 8 NICs × 50 GB/s (400 Gb/s each) = 400 GB/s
measured busbw  ≈ 350 GB/s  → 350 / 400 = 88 % of node egress   [SIMULATED data, MODELED ratio]
```

The intra-node legs run on NVLink (≈ 450 GB/s per direction), which is faster, so the inter-node NIC
hop is the bottleneck, and ≈ 88 % is a normal efficiency once protocol overhead, flags and congestion
control are paid. A single NIC at 50 GB/s would cap busbw near 45 GB/s only for a rail-pinned
communicator of one GPU per node.

**Common wrong answers.** Comparing busbw with one NIC's 50 GB/s and concluding the number is
impossible; confusing algbw with busbw; claiming NVLS/SHARP is required (it is not for this value).
