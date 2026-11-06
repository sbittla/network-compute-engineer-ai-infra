# 10.T1 — "Leaf r6 uplinks are dirty"

**(a) Is it physical? The five discriminating questions (Section 10.8.1)**

1. *Is the error load-dependent?* Yes. Discards and PFC pause frames rise only from 01:00 to 01:20,
   exactly the MoE evaluation job's all-to-all window. Corruption does not switch on with one job;
   congestion does.
2. *Is it one link, one direction?* No. All eight uplinks to spine-1 change together. Physical
   faults are local to one link; simultaneous symptoms on every member of a bundle point at a
   shared bottleneck (spine-1 and its downstream ports).
3. *Is there a physical precursor?* No. FEC-uncorrectable = 0 and FCS = 0 on all eight ports.
4. *Do DOM and FEC agree?* Yes, and both are clean: pre-FEC BER 10⁻⁸–10⁻⁷ (≥ 3.4 decades of margin to
   2.4 × 10⁻⁴) and DOM normal.
5. *Is it configuration?* Possibly, but not optics: ECMP hashing that concentrates low-entropy RoCE
   flows on spine-1 (Chapter 7), or buffer/PFC thresholds, could make one spine hotter.

**Conclusion: not physical.** It is congestion from the cross-rail expert-parallel all-to-all
(Chapter 12) converging on spine-1, possibly made worse by ECMP polarization. It belongs to the
Chapter 9 congestion workflow. Cleaning eight healthy links would add risk (eight drains, eight
chances to damage an end-face) and fix nothing.

**(b) Missing evidence and how to collect it safely (all reads, no changes)**

| Missing item | Source / command |
|---|---|
| Spine-1 egress queue depth, discards, PFC sent and ECN marks on the ports toward the destination leaves | Switch streaming telemetry or `show interfaces counters` / queue counters on spine-1 (read-only) |
| Per-uplink throughput for r6's uplinks to spines 1–4 during 01:00–01:20 | Interface rate telemetry; shows ECMP imbalance if spine-1 carries more than spines 2–4 |
| Host NIC PFC, ECN and CNP counters on the job's nodes | `ethtool -S <if>` (read-only), RDMA `hw_counters` under `/sys/class/infiniband/<dev>/ports/1/hw_counters` |
| The job's all-to-all pattern: rank map, expert placement, whether PXN is enabled | Job config and NCCL `INFO` logs (Chapter 12); Training Infra owns it |

**(c) Owner and ticket update**

Owner: **Fabric (congestion/QoS)**, with **Training Infra** for the job's communication pattern.
Ticket text: "Cleaning not required: all eight uplinks show zero FEC-uncorrectable and zero FCS, clean
DOM and pre-FEC BER of 10⁻⁸–10⁻⁷; discards and PFC appear only during the 01:00–01:20 MoE all-to-all
window on every spine-1 uplink, which indicates congestion. Re-routed to the Fabric congestion
workflow (Chapter 9) with a request for spine-1 queue telemetry and the job's traffic analysis."

**Common wrong answers.** Approving the cleaning because "discards are errors"; treating PFC received
as a physical symptom; asking for a change (ECMP or PFC tuning) before collecting spine-side evidence.
