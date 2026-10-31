# K1 — DCQCN roles in the 12:1 incast (worked solution)

Relies on manuscript Section 9.6 ("Three roles", Table 9.2a, Figure 9.8) and Section 9.7 (the 12:1
incast: twelve ORION nodes sending to `orion-n05` on rail 3).

| DCQCN role | Device in the 12:1 incast | What it does |
|---|---|---|
| **CP**, congestion point | The **`orion-be-leaf-r3` egress queue on eth1/5** (TC 3, toward `orion-n05`) | Its queue exceeds Kmin, so it marks ECT packets CE with probability p(q) (RED/ECN profile) |
| **NP**, notification point | **`orion-n05`'s NIC, `mlx5_3`** (the receiver) | Sees CE-marked packets and returns at most one CNP per flow per interval N (50 µs) |
| **RP**, reaction point | **Each of the 12 sending NICs** (their rail-3 `mlx5_3`) | On each CNP: Rt = Rc, Rc ← Rc × (1 − α/2), α ← (1 − g)α + g; then recovers |

**The NP → RP packet** is the **Congestion Notification Packet (CNP)**: a small RoCEv2 packet (BTH
opcode 0x81) addressed to the sending QP. ORION carries it in **DSCP 48 → TC 6, strict priority**, so
feedback never waits behind the congestion it reports. RoCE data itself is DSCP 26 / TC 3.

On the NICs the roles are visible in the counters: `np_cnp_sent` on `orion-n05` (≈ 400,000 CNPs/s in
the lab's incast episode, `[SIMULATED]`) and `rp_cnp_handled` on the senders.

**Common mistake:** naming the switch as the CNP sender. In RoCEv2 DCQCN the switch only marks (CP);
the **receiver NIC** generates CNPs (NP). Another mistake is putting CNPs in TC 3 (see K4).
