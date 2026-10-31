# D1 — A second lossless class? (model recommendation)

Numbers `[MODELED]` (`solve.py`). Relies on manuscript Section 9.4 (Table 9.2 headroom), Section 9.5
(risks of PFC), Section 9.9 (lossy RoCE and newer transports), "Trade-offs and design decisions", and
docs/REFERENCE_CLUSTER.md (frontend/storage fabric 2 × 200 GbE per node; W-TRAIN checkpoint size).

## Recommendation

**Reject a second lossless priority on the backend. Accept the checkpoint RDMA traffic with
conditions: in a lossy, ECN-enabled class on the backend, or (preferred, ORION's design intent) on the
frontend/storage fabric.**

## Headroom cost of priority 4

Per (port, lossless priority), H = 2 × 9,216 + 2 × 50 × L × 5 + 50,000 + 64:
- 30 m host port: **83,496 B**; 100 m spine port: **118,496 B**.
- Rail leaf: 32 × 83,496 + 32 × 118,496 = 2,671,872 + 3,791,872 = **6,463,744 B ≈ 6.5 MB** extra.
- Each spine (64 × 100 m): 64 × 118,496 = **7,583,744 B ≈ 7.6 MB** extra.

That buffer comes out of the shared pool that absorbs W-TRAIN's TC 3 bursts.

## Interaction with W-TRAIN's TC 3, and other risks

1. **Less burst absorption for TC 3.** About 6.5 MB less shared buffer per leaf means queues reach Xoff
   sooner in collectives, so there are more pauses and a higher p99.
2. **Cross-class HOL blocking.** Checkpoint bursts (≈ 980 GB per W-TRAIN checkpoint) pause priority 4
   on ports and NICs that also carry TC 3 collectives. They share egress links, NIC pipelines and buffer
   pools, so a pause storm or congestion tree in one class degrades the other.
3. **A second set of congestion trees, storms and watchdog actions** to operate, and a **doubled
   deadlock surface**.
4. **Configuration drift.** Every switch and NIC must agree on two lossless priorities. That is exactly
   the lab's `orion-be-spine-2 PFC_PRIORITY_MISMATCH` fault.

"Cannot tolerate loss" conflates **transport reliability** with **network losslessness**. RDMA RC is
reliable over a lossy network; the real question is retransmission cost. Checkpoint writes are bulk and
latency-tolerant, so they can afford it, especially with selective-repeat NICs.

## Alternatives

| Option | Cost | Isolation from TC 3 | Risk | Maturity |
|---|---|---|---|---|
| **A. Frontend/storage fabric** (2 × 200 GbE per node) for checkpoints | None new (existing design intent) | Full: separate fabric | Lower bandwidth (400 Gb/s per node) | Standard |
| **B. Lossy backend TC with ECN/DCQCN** + NIC selective retransmission | Config and validation effort | Good: separate queue, no pauses, DWRR weight | Retransmissions during bursts; needs NIC capability proof | Vendor-dependent `[VENDOR-SPEC, 2026-10]` |
| C. Rate-limit or schedule checkpoints (staggered, paced) | Engineering in the checkpoint client | Partial | Longer checkpoint windows | Easy |
| D. Second lossless class (requested) | 6.5 MB per leaf, 7.6 MB per spine, operational load | Poor (pauses shared ports and NICs) | Storms, deadlock, drift, TC 3 impact | Possible, risky |

**Conditions for acceptance (B or A):** checkpoint traffic marked into its own DSCP and queue with ECN,
never PFC; DWRR weight below TC 3; pacing in the checkpoint client; monitoring of retransmission
counters and checkpoint duration.

## What would change the decision

Measured evidence from an L3 lab fabric that loss recovery for the checkpoint path is unacceptable
(for example, checkpoint time or job stalls outside the SLO even with selective repeat and pacing),
**and** a headroom budget that shows no measurable impact on TC 3 burst absorption (a switch with
enough buffer that the extra ≈ 6.5 MB is small, verified with TC 3 pause and p99 measurements in an
A/B).
