# 8.8 — Wire efficiency and DSCP marking (worked solution)

All numbers `[MODELED]`. Relies on manuscript Section 8.7 (per-packet overhead, Table 8.4) and the
ORION QoS policy (Section 8.4; Chapter 7 Table 7.6: DSCP 26 → TC 3 lossless, DSCP 48 → TC 6 CNPs).
`solve.py` recomputes every value.

**Base per-packet wire overhead** (RDMA WRITE Middle packet, untagged IPv4): preamble + SFD 8 +
Ethernet 14 + IPv4 20 + UDP 8 + BTH 12 + ICRC 4 + FCS 4 + inter-frame gap 12 = **82 B**.

## (a) 2,048-byte path MTU, VLAN-tagged, IPv4

Overhead = 82 + 4 (802.1Q tag) = **86 B**.
Efficiency = 2,048 / (2,048 + 86) = 2,048 / 2,134 = **0.9597**.
Payload ceiling = 400 Gb/s × 0.9597 = **383.9 Gb/s**.

## (b) 4,096-byte path MTU, untagged, IPv6

The IPv6 header is 40 B instead of 20 B: overhead = 82 + 20 = **102 B**.
Efficiency = 4,096 / (4,096 + 102) = 4,096 / 4,198 = **0.9757**.
Payload ceiling = 400 × 0.9757 = **390.3 Gb/s** (against 392.1 Gb/s for IPv4 in Table 8.4).

## (c) Packet rate at line rate for (b)

Packets/s = line rate / bits per packet on the wire = 400 × 10⁹ b/s / (4,198 B × 8 b/B) =
400 × 10⁹ / 33,584 = **11.91 M packets/s**.

## (d) `NCCL_IB_TC=26`

`NCCL_IB_TC` sets the **whole 8-bit IP traffic-class byte** (DSCP in the upper 6 bits, ECN in the lower
2), not the DSCP.

26 = 0b**000110**|**10**
- DSCP = upper 6 bits = 0b000110 = **6**
- ECN = lower 2 bits = 0b10 = **ECT(0)**

ORION's switches map only DSCP 26 → TC 3 and DSCP 48 → TC 6, so DSCP 6 falls into the **default lossy
class (TC 0)**. There is no PFC protection, and the traffic shares a queue with best-effort traffic. It
is ECN-capable, but whether TC 0 has an ECN profile depends on switch policy. The intended marking is
DSCP 26 with ECT(0): 26 × 4 + 2 = **106**, so `NCCL_IB_TC=106`.

## Common mistakes

- Leaving out preamble/SFD and IFG. That gives frame efficiency (98.5 % at 4,096), not wire
  efficiency.
- Treating `NCCL_IB_TC` as a DSCP value and concluding that 26 lands in TC 3.
- Adding the VLAN tag in (b), or using 4,096 + 82 for IPv6.
