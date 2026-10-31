# 7.K3 — MTU mismatch and the eBGP session (worked solution)

Relies on manuscript Section 7.4 ("What 'MTU' means depends on who you ask", "Path MTU discovery and
why it fails in fabrics").

## Why the eBGP session comes up and stays up

BGP runs over TCP. In the SYN handshake each endpoint advertises a **maximum segment size (MSS)**
derived from its *own* interface MTU:

- 9216 side: MSS ≈ 9216 − 20 (IP) − 20 (TCP) = **9,176 B**
- 1500 side: MSS = 1500 − 40 = **1,460 B**

A TCP sender never sends a segment larger than the MSS its peer advertised. The 9216 side therefore
sends at most 1,460-byte segments (because the 1500 side advertised 1,460), and the 1500 side sends at
most 1,460-byte segments (its own MTU). Every BGP packet fits in a 1500-byte IP packet, so OPENs,
UPDATEs and keepalives all get through, and the session reaches and stays **Established**. BGP
UPDATEs can be up to 4,096 B (or 65,535 B with RFC 8654 extended messages); the reason they survive
is MSS segmentation, not "BGP packets are small".

## Which traffic fails

Data traffic routed over the link, not BGP, fails, and it fails **in both directions** by different
mechanisms:

| Direction | What happens to a large packet | Visible where |
|---|---|---|
| 9216 end → 1500 end | The 9216 side transmits a frame up to ≈ 9.2 KB; the 1500 port's MAC drops it at **ingress** as oversize ("giant") | Giant/oversize counter on the 1500 port; no ICMP is generated |
| 1500 end → 9216 end (traffic routed *out of* the 1500 interface) | A packet > 1500 B fails the **egress MTU check** and is dropped (ICMP "fragmentation needed" if DF is set and ICMP generation is not rate-limited away) | MTU-exceeded drop counter; often silent in practice |

For the AI backend this hits RoCEv2 directly: a 4,096-byte path MTU produces 4,174-byte frames
(7.K4), larger than 1500, so every RDMA flow that ECMP hashes onto this link loses its data packets
while small-packet tests (ping with default size, BGP) look healthy. This is the lab's planted
`MTU_MISMATCH` on `F-r3-s2-k6`.

## Common wrong answers

- "BGP packets are small" without the MSS mechanism (1 of 2 points).
- Saying loss occurs only in one direction: both directions lose large packets.
- Expecting PMTUD to rescue RDMA: RoCEv2 is UDP with a fixed path MTU chosen at QP setup, and it
  ignores ICMP "fragmentation needed".
