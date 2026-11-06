# 13.7 — One pipeline message, two paths: worked solution

**Message.** M/t = 67.1 MB / 8 = **8.39 MB** activation, sent from a stage on one ORION node to the next
stage on another node. Path counting follows Table 13.2 (Section 13.4).

| Path | Host-DRAM copies | PCIe transfers | PCIe bytes | Time `[MODELED]` |
|---|---|---|---|---|
| GPUDirect RDMA | 0 | 2 (NIC reads sender GPU; remote NIC writes receiver GPU) | 2 × 8.39 = **16.8 MB** | 8.39e6 B / 45e9 B/s = **186 µs** (+ ≈ 10 µs fixed) |
| Host-staged, unpipelined | 2 (one per side) | 4 (GPU→host by the NCCL kernel, host→NIC, NIC→host, host→GPU by the NCCL kernel) | 4 × 8.39 = **33.6 MB** | 168 + 186 + 168 = **522 µs** |

**Arithmetic.**

```text
GDR:         t = S / B_nic          = 8.39e6 / 45e9   = 186.4 µs
staging copy t = S / B_copy         = 8.39e6 / 50e9   = 167.8 µs (each side)
host-staged  t = copy + wire + copy = 167.8 + 186.4 + 167.8 = 522.0 µs (upper bound)
```

The host-staged time is an *upper bound* because it assumes the three stages run one after another.
NCCL chunks messages and pipelines the stages, so in practice the time approaches ≈ 186 µs plus one
chunk's copy latency. Pipelining does not remove the costs that matter at scale: PCIe bytes double
(33.6 vs 16.8 MB), each byte crosses the PCIe switch uplink to the socket twice per side, and host DRAM
absorbs a write and a read on both nodes. On the fill and drain phases of the pipeline schedule these
messages are on the critical path, so the extra latency adds directly to step time (Section 13.11,
Step 2).

**Labels.** Bandwidths 45 GB/s and 50 GB/s are `[ILLUSTRATIVE]` inputs from the prompt. Every result is
`[MODELED]`. The ≈ 10 µs fixed cost is an `[ILLUSTRATIVE]` NCCL-hop allowance from Section 13.4.

**Common wrong answers.** Counting NCCL's internal HBM copy as a host copy. Using 400 Gb/s = 50 GB/s for
the NIC instead of the stated 45 GB/s effective. Reporting the 522 µs as the expected time rather than an
unpipelined bound.
