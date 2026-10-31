# 8.4 — RoCEv1 versus RoCEv2 (worked solution)

Relies on manuscript Section 8.4 (RoCEv2 encapsulation, GID table) and Section 8.13 (the GID-index
troubleshooting scenario). Counter names are mlx5-style and vendor-specific (`[VENDOR-SPEC, 2026-10]`).

## Encapsulation difference

| | RoCEv1 | RoCEv2 |
|---|---|---|
| Layering | Ethernet header with **EtherType 0x8915**, then the IB GRH (40 B) + BTH; **no IP header** | Ethernet → **IPv4/IPv6 → UDP (destination port 4791)** → BTH |
| Scope | One Layer 2 broadcast domain (bridged only) | Routable across L3 hops; ECMP-hashable (UDP source port = entropy) |
| QoS marking | 802.1p PCP only | DSCP in the IP header (ORION: 26 → TC 3) |

The GID table on a RoCE NIC holds both a v1 and a v2 entry for each address. The GID *index* the QP
uses (`NCCL_IB_GID_INDEX`, perftest `-x`) decides which encapsulation goes on the wire.

## Why v1 cannot work on ORION's backend

ORION's backend is **routed to the host**: each NIC sits on its own /31 to its rail leaf, and the leaf
forwards by IP longest-prefix match. A v1 frame is addressed to the next hop's MAC (the leaf), but it
carries no IP header. The leaf receives a frame with an EtherType it does not route and has no L2
domain to bridge it into, so it **drops it**. Nothing reaches the peer: no data, no ACKs.

## Counter-level signatures

**On the leaf** (host-facing port of the misconfigured node):
- ingress drops of non-IP / unknown-EtherType (or "unknown protocol") frames rising at the rate the
  host transmits;
- **zero RoCE packets** from that port in the RoCE class (no UDP 4791 / DSCP 26 → TC 3 traffic, TC 3
  counters flat) while the host claims to send.

**On the hosts:**
- `local_ack_timeout_err` rising on the **requester side of both peers** (nothing is ever ACKed);
- NCCL fails with `error 12` = `IBV_WC_RETRY_EXC_ERR` after (retry_cnt + 1) × T_ack;
- **no `out_of_sequence` or `packet_seq_err`**: nothing arrives at all, so the responder never sees a
  PSN gap. This separates a total black hole from partial loss.

## Common mistakes

"v1 is just older and slower": the issue is reachability, not speed. Expecting ICMP errors: the switch
sends none for a non-IP frame.
