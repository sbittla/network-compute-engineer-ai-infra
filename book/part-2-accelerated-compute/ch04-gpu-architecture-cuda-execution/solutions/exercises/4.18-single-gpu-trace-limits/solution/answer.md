# 4.18 — What a single-GPU trace cannot tell you about 256 GPUs (model answer)

Relies on manuscript Section 4.1 and "Realism boundaries"; forward references per the chapter map.

Any two, each with mechanism and chapter:

1. **Collective communication time and its overlap with compute.** At 256 GPUs every step contains
   all-reduce/all-gather/reduce-scatter traffic over NVLink and the RDMA fabric; whether it hides behind
   backward compute depends on bucket sizes, streams and the fabric. A single-GPU trace has no collectives at
   all. Chapters 11–12 (distributed training architecture; collective communication and NCCL).
2. **Stragglers and rank skew.** A synchronous job runs at its slowest rank; one throttled GPU or slow host
   stalls all 256. One GPU cannot show the distribution across ranks. Chapters 6 (variance) and 12.
3. **Network congestion and fabric effects** (incast, ECN/PFC behaviour, tail latency of collectives):
   Chapter 9 (with Chapters 7–8 for the fabric itself).
4. **Topology effects** such as GPU–NIC locality, rail alignment and GPUDirect RDMA paths: Chapter 5, with
   GPU data movement across nodes in Chapter 13.

A single-GPU trace remains the right first step: it removes local waste (pageable copies, syncs, launch
overhead) that would otherwise be multiplied by every rank.

(≈ 150 words.)
