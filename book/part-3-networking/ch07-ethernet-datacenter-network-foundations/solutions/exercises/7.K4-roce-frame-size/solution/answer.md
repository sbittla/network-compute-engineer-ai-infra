# 7.K4 — RoCEv2 frame size and the RDMA path MTU (worked solution)

All numbers `[MODELED]`. Relies on manuscript Section 7.4 ("RoCEv2 frames and the RDMA path MTU",
Figure 7.2). `solve.py` recomputes every value.

## Header-by-header sum (RDMA WRITE first packet, IPv4, untagged)

| Field | Bytes | Running total |
|---|---|---|
| Ethernet header (dst MAC, src MAC, EtherType) | 14 | 14 |
| IPv4 header | 20 | 34 |
| UDP header (destination port 4791) | 8 | 42 |
| BTH (base transport header) | 12 | 54 |
| RETH (RDMA extended transport header, first packet of a WRITE) | 16 | 70 |
| Payload (path MTU 4,096) | 4,096 | 4,166 |
| ICRC (invariant CRC) | 4 | 4,170 |
| FCS (Ethernet frame check sequence) | 4 | **4,174** |

Frame on the wire including FCS = **4,174 B**; the IP packet (IPv4 through ICRC) is 4,156 B. Middle
packets of the WRITE carry no RETH: 4,158-byte frames. Preamble and inter-frame gap are not part of
the frame.

## Active RDMA MTU with a 1500-byte netdev MTU

RoCEv2 devices pick the largest InfiniBand path MTU (256, 512, 1,024, 2,048, 4,096) whose packet fits
under the netdev IP MTU. Space for payload = 1500 − 20 (IP) − 8 (UDP) − 12 (BTH) − 4 (ICRC) =
**1,456 B**, and 16 B less (1,440 B) on a packet that carries a RETH. 2,048 does not fit, so the
device selects **1,024**, as `ibv_devinfo` shows: `active_mtu 1024 (3)`. That agrees with
docs/VERIFIED_FACTS.md: "A 1500 B netdev MTU caps `active_mtu` at 1024".

## Why ORION sets host MTU 9000 when RoCE frames are only ≈ 4.2 KB

The 9000-byte MTU does not carry RoCE frames. It lets the device **select** path MTU 4,096, which
needs an IP MTU of at least 4,156 B (roughly 4,200 B). 4,096-byte packets mean 4× fewer packets
than 1,024 for the same message: fewer per-packet header bytes, ACKs and NIC/switch packet-rate
costs. The 9000 MTU also gives jumbo frames to any TCP traffic on the backend NICs. The switch ports
run 9216, which leaves headroom above both 9,022-byte tagged host frames and 4,174-byte RoCE frames.

## Common wrong answers

- Claiming RoCE frames are ≈ 9 KB: the RDMA path MTU caps them at 4,096 B of payload.
- Counting 4,158 B without saying RETH was excluded (accepted only if stated).
- Picking 2,048 at netdev MTU 1500: 2,048 + 44 B > 1,500.
