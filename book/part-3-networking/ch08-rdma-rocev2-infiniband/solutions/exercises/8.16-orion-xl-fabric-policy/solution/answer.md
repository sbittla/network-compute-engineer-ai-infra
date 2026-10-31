# 8.16 — ORION-XL fabric policy (model answer)

Open-ended: grade the reasoning. This model answer chooses RoCEv2. An InfiniBand answer is equally
valid if it covers SM scale (sweep time, redundancy), partitioning, and adaptive-routing dependencies.
Numbers `[MODELED]` unless marked; `solve.py` recomputes them. Relies on manuscript Sections 8.6
(Table 8.3), 8.7, 8.8, 8.9, Table 8.10, and docs/REFERENCE_CLUSTER.md §4 (ORION-XL: 512 HX8 nodes,
16 pods of 32 nodes, 3-tier Clos; job MTBF ≈ 3 h).

## Decision and criteria

**RoCEv2, lossless on the RoCE class (PFC priority 3) with ECN/DCQCN tuned to act first, so PFC is
only a safety net.** Criteria: (1) continuity with ORION-256's tooling, automation and skills; (2) a
multi-vendor supply chain at 4,096 NICs; (3) a loss model compatible with the NIC recovery we can
*prove*. The loss model depends on **go-back-N** RC recovery, the assumed capability of the NIC
generation. If the selected NIC's selective repeat is validated at L3 (`[VENDOR-SPEC, 2026-10]`), run
a lossy-RoCE pilot on one pod before changing the fabric-wide policy.

## Parameters

| Parameter | Value | Justification |
|---|---|---|
| 3-tier round trip | **10 µs** `[ILLUSTRATIVE]` (leaf–spine–core–spine–leaf, including queueing headroom) | Five switch hops each way plus longer cables than ORION-256's 5 µs cross-rail RTT |
| BDP at 392 Gb/s | 49,000 B/µs × 10 µs = **490,000 B ≈ 120 packets** of 4,096 B | Sizes ECN Kmin (≤ 1 BDP) and the go-back-N waste per loss (≈ 1 RTT, 10 µs) |
| ACK timeout | **`timeout` 20** → T_ack = 4.096 µs × 2²⁰ = **4.29 s** | Rides through long PFC pauses and link flaps; NCCL ≥ 2.23 default (`[VENDOR-SPEC, 2026-10]`) |
| Retry count | **`retry_cnt` 7** → time to failure 8 × 4.29 = **34.4 s** | A dead peer is detected within a minute |
| Path MTU | **4,096** on every NIC; host netdev 9000; switch ports 9216 | Fewest packets; automated switch MTU compliance at every tier |
| GID/addressing | Per-NIC routed /31 per rail and pod; GID = `RoCE v2` entry carrying the rail IP, derived and validated per host (or rdma_cm) | The GID-index fault (8.4, 8.20) must be impossible at admission |
| QoS | DSCP 26 → TC 3 lossless + ECN; CNP DSCP 48 → TC 6 strict; `NCCL_IB_TC=106` | Same as ORION-256, verified on every tier |

## Quantified trade-off: timeout length

At the design loss rate p = 10⁻⁷ per packet, an isolated 4 MiB message (85.6 µs) pays an expected
tail-loss cost of p × T_ack:

| `timeout` | T_ack | Time to failure | Tail cost per message | Share of a 4 MiB message |
|---|---|---|---|---|
| 14 | 67.1 ms | 0.54 s | 0.0067 µs | 0.008 % |
| 18 | 1.07 s | 8.59 s | 0.107 µs | 0.13 % |
| **20** | **4.29 s** | **34.4 s** | **0.43 µs** | **0.50 %** |

Choosing 20 costs ≈ 0.5 % in expected tail-loss time, acceptable for MiB-scale messages. A short timeout
(14) would turn every PFC pause or link flap longer than ≈ 0.5 s into a fatal `IBV_WC_RETRY_EXC_ERR`.
Each spurious failure costs a **4,096-GPU restart** from checkpoint, in a job whose MTBF is already
≈ 3 h. If the loss rate were 10⁻⁵, the same timeout would cost 43 µs per isolated message (≈ 50 % of the 85.6 µs transfer, so goodput ≈ 67 %):
the policy is only valid if the fabric really is near loss-free, which must be monitored.

## Readiness checklist at 512 nodes

- Fully **automated in the admission pipeline**: no human runs the checklist.
- **100 % of nodes on every change**: no sampling for configuration checks. Sampling suits only
  expensive load tests.
- Switch-side compliance across all three tiers from the config-compliance system.
- Peer validation per rail against a **rotating reference node** in each pod, with results compared to
  the fleet median (Lab 8 logic).
- **Admission gates**: a node fails closed (drained) on any finding.

## Single NIC failure mid-job

NCCL reports an error, or the job hangs until the timeout above. The job restarts from checkpoint
**excluding the node** (Chapter 19; ORION-XL can hold spares). Do not run degraded at 7/8 rails for a
long job: synchronous collectives run at the slowest node's pace.

## Accepted risk and detection

**Accepted risk: PFC storms and pause propagation across three tiers** (lossless at 4,096 NICs).
Detection: PFC watchdog enabled on every port with alerts; pause-duration and pause-rate counters per
port (Chapter 9) with an alert on any sustained pause tx from a host-facing port; the ECN-mark/pause
ratio tracked per leaf to catch "running on pause".

## Common mistakes

Choosing a short timeout "for fast failure" without the restart cost. Quoting a BDP without a stated
RTT. Sampling configuration checks.
