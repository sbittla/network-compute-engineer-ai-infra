# 8.9 — The price of a lost packet (worked solution)

All numbers `[MODELED]`; the 5 µs cross-rail RTT is `[ILLUSTRATIVE]` (docs/REFERENCE_CLUSTER.md).
Relies on manuscript Section 8.6 (go-back-N, T_ack = 4.096 µs × 2^timeout, Table 8.3, "Why loss is so
expensive") and Section 8.7 (392 Gb/s ceiling at 4,096). It agrees with docs/VERIFIED_FACTS.md ("RC
go-back-N loss cost"). `solve.py` recomputes every step.

**Assumptions:** one QP; the payload ceiling 392 Gb/s = 49.0 GB/s = 49,000 B/µs; go-back-N (no
selective repeat); NAK processing time ignored; independent per-packet loss.

## (a) Packets and loss-free time

Packets = 1,048,576 B / 4,096 B = **256**.
Time = 1,048,576 B × 8 / (392 × 10⁹ b/s) = 8,388,608 / 392 × 10⁹ = **21.4 µs**.

## (b) Packet 50 lost, go-back-N

Bandwidth-delay product: BDP = 49,000 B/µs × 5 µs = **245,000 B** ≈ 245,000 / 4,096 = **60 packets**.

Packet 51 reaches the responder, which sees the PSN gap, NAKs packet 50, and discards everything until
packet 50 arrives again. The NAK reaches the requester about one RTT after it sent packet 50. During
that RTT it has sent packets 51 … ≈ 110, about one BDP, all discarded and resent.

Extra time ≈ wasted transmission = 60 × 4,096 × 8 / 392 × 10⁹ = **5.0 µs ≈ one RTT**, i.e.
5.0 / 21.4 ≈ **23 %** longer. (5–10 µs is accepted if NAK processing is added and stated.) Only the
in-flight window is wasted, not packets 50–256. Those would have been sent anyway.

## (c) Last packet lost, `timeout` = 18

No later packet can expose the gap, so no NAK. The requester waits the local ACK timeout:
T_ack = 4.096 µs × 2¹⁸ = 4.096 µs × 262,144 = **1.074 s** extra. That is ≈ 50,000× the 21.4 µs transfer.

## (d) Expected goodput with p = 10⁻⁵, isolated messages

For an isolated message (the QP idles afterwards), only a lost **final packet** (or final ACK) costs
a timeout. Assume first that the ACK path is loss-free:
- tail cost per message ≈ p × T_ack = 10⁻⁵ × 1.074 s = **10.7 µs**;
- mid-message losses: 256 × 10⁻⁵ = 0.00256 losses per message × ≈ 5 µs = 0.013 µs (negligible).

Goodput ≈ 21.4 / (21.4 + 10.7 + 0.013) ≈ **0.67 → ≈ 67 %**. A one-in-100,000 loss rate costs a third
of throughput. If the final ACK crosses an equally lossy path, the probability is ≈ 2p: 21.5 µs per
message and goodput ≈ 21.4 / (21.4 + 21.5) ≈ **50 %**.

**Back-to-back messages:** the next message's first packet exposes a lost tail and triggers a NAK
(≈ one RTT of cost), so the timeout risk applies only to the *last* packet of each burst. With bursts
of *k* messages the timeout cost is ≈ 10.7 / *k* µs per message: goodput ≈ 89 % for k = 4, ≈ 97 % for
k = 16. Collectives that pause between steps still pay it once per burst. The lesson: with long
timeouts the fabric must be effectively loss-free (PFC + ECN), or the NIC must recover tail loss faster
(selective repeat, `[VENDOR-SPEC, 2026-10]`).

## (e) Time to `IBV_WC_RETRY_EXC_ERR` if the peer dies

Each timeout consumes one retry, and the error is raised after the original attempt plus `retry_cnt`
retries: (retry_cnt + 1) × T_ack = (7 + 1) × 1.074 s = **8.59 s** (Table 8.3).

## Common mistakes

- Counting packets 50–256 as waste in (b).
- Applying p × T_ack to every message of a continuous stream in (d).
- Using 7 × T_ack in (e).
- Using 400 Gb/s instead of the 392 Gb/s payload ceiling (small error, but say which).
