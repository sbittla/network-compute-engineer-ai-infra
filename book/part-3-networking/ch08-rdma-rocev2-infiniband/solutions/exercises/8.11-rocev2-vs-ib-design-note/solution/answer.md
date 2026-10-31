# 8.11 — RoCEv2 versus InfiniBand design note for ORION's backend (model answer)

Relies on manuscript Sections 8.4, 8.5, 8.6 (Table 8.3), 8.7 (Table 8.4), 8.8 and 8.9 (Table 8.5), and
docs/VERIFIED_FACTS.md (NCCL timeout defaults). Either recommendation earns full marks if it is
criteria-driven. A model RoCEv2 note follows.

## 1. Comparison (four mandated dimensions)

| Dimension | RoCEv2 | InfiniBand |
|---|---|---|
| **Transport** | IBA transport (BTH, RC) in UDP/IP, destination port 4791; ECMP entropy from the UDP source port per QP; lossless only if PFC is configured; go-back-N recovery (selective repeat on newer NICs, `[VENDOR-SPEC, 2026-10]`) | Native IBA (LRH, BTH); credit-based link flow control per VL, so no congestion drops by design; FECN/BECN congestion control, adaptive routing |
| **Fabric management** | Distributed: per-switch BGP control plane; QoS/PFC/ECN and MTU pushed to every switch and NIC by automation | Centralized subnet manager: discovery, LIDs, routing tables, partitions; the SM is a critical service needing redundancy |
| **Operational model** | Same tooling, skills, monitoring and spares as Halcyon's Ethernet estate; multi-vendor | Specialist skills, typically single-vendor; separate tooling |
| **Troubleshooting evidence** | Switch queue depth/watermarks, ECN-marked, PFC tx/rx per priority, discards, FEC/CRC; NIC `rdma statistic` (`out_of_sequence`, `local_ack_timeout_err`, `np_cnp_sent`), `ethtool -S` pause counters | `perfquery` (`PortXmitWait`, `SymbolErrorCounter`, `PortRcvErrors`), `ibdiagnet`, SM logs, `ibstat` port states |

## 2. Recommendation and criteria

**Recommend RoCEv2, lossless on the RoCE class (PFC priority 3 + ECN/DCQCN).** Criteria, in order:
(1) operability by the existing Fabric team, which already automates BGP leaf-spine fabrics;
(2) one network technology and vendor choice across frontend and backend; (3) performance within a
few percent of InfiniBand for ORION's rail-aligned traffic; (4) risk that can be controlled by
automation. Lossless is chosen because ORION's NICs are assumed to be go-back-N (8.9: at p = 10⁻⁵ a
lost tail costs ≈ 33 % goodput). The accepted cost is high configuration risk. It is mitigated by the
Lab 8 readiness validator (hosts), switch config compliance checks, and the Lab 7 intent validator.

## 3. Parameters (every number labelled)

- **Addressing/GID:** host `10.100.r.(2n+1)/31` on rail *r* `[ILLUSTRATIVE]`, per-rail policy routing.
  The GID index is the `RoCE v2` GID entry carrying the rail IP, validated on every NIC (rdma_cm resolves it
  automatically).
- **QoS:** DSCP 26 → TC 3 (PFC + ECN), CNP DSCP 48 → TC 6 strict priority. The `NCCL_IB_TC` byte =
  DSCP × 4 + ECN = 26 × 4 + 2 = **106** `[MODELED]`.
- **MTU at three layers:** host netdev **9000** → `active_mtu` **4096**; RDMA path MTU **4096**; switch
  ports **9216**. The largest RoCE frame is 4,158 B (4,174 B with RETH) ≤ 9216 ✓ `[MODELED]`.
- **ACK timeout/retry:** `timeout` 18 (T_ack = 1.07 s) with `retry_cnt` 7 → time to failure
  8 × 1.07 = **8.6 s**. Or `timeout` 20 (4.29 s) → **34.4 s** `[MODELED]`. Choose 18–20: long enough to
  ride through PFC transients and link flaps, short enough to fail a dead peer within a minute. The
  NCCL default is 18 up to 2.22 and 20 from 2.23 `[VENDOR-SPEC, 2026-10]`, so state the version.
- **Multi-rail failure:** one rail lost = −12.5 % of the node's 8 × 392 = 3,136 Gb/s `[MODELED]`. A
  synchronous job runs at the degraded node's pace, so the policy is to drain and replace rather than
  run degraded through a long job.

## 4. Three most likely failure signatures (RoCEv2)

1. **Mis-marked traffic in a lossy queue** (wrong `NCCL_IB_TC`, untrusted port): drops under load,
   `out_of_sequence` and NAKs rising, no PFC on TC 3.
2. **PFC storm / pause propagation** (Chapter 9): sustained pause tx from one NIC, victim flows with
   high p99 latency, deep queues with zero egress.
3. **Switch-port MTU mismatch or wrong GID index**: connects, small messages pass, large transfers hit
   `IBV_WC_RETRY_EXC_ERR`; leaf oversize-drop counters rise (8.15), or no RoCE traffic leaves at all
   (8.4).
(Also: optics/FEC degradation causing CRC drops, Chapter 10.)

## 5. Cross-references

Congestion control, PFC headroom and watchdogs: Chapter 9. Optics, FEC and cabling evidence:
Chapter 10.

## Common mistakes

Claiming IB "never congests" (it back-pressures). Claiming RoCEv2 *requires* PFC (lossless is a
design choice tied to NIC recovery). Unlabelled numbers.
