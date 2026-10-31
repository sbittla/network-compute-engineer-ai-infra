# 8.5 — Entropy from the UDP source port (worked solution)

Relies on manuscript Section 8.4 (RoCEv2 header fields), Section 8.8 (multi-rail design) and Chapter 7
Section 7.6 (per-flow ECMP, low entropy).

## The role of the UDP source port

In RoCEv2 the UDP destination port is fixed (4791), and the IP addresses are fixed per NIC pair. The
**UDP source port is the only per-flow entropy** that switch ECMP hashing (5-tuple) can use. The NIC
typically derives one source port per QP. A QP's packets therefore always hash to the **same path**,
which preserves ordering (important for go-back-N, Section 8.6), and different QPs can land on different
paths.

## Why bandwidth varies between identical runs

A rail-to-rail all-to-all that crosses the spine with **two QPs per NIC pair** presents only a few
elephant flows per leaf to ECMP. Hashing balances *flows*, not bytes, so two heavy QPs can hash onto the
same spine uplink while another uplink idles. The colliding flows then share 400 Gb/s and run at
≈ 200 Gb/s each. Every run creates new QPs with **different QP numbers, so different source ports and
different hash results**. Which flows collide changes from run to run, giving noisy or **bimodal**
bandwidth with no configuration change. A collective finishes with its slowest flow, so one collision
can set the whole step time. Chapter 7: 8 flows on 8 links use only ≈ 5.25 links on average
`[MODELED]`.

## Mitigations (any two, each with its trade-off)

| Mitigation | Effect | Trade-off |
|---|---|---|
| **More QPs per connection** (`NCCL_IB_QPS_PER_CONNECTION`, default 1, `[VENDOR-SPEC, 2026-10]`) | More, smaller flows spread better statistically | More NIC QP state, memory and completion processing; smaller per-QP messages |
| **Rail-local placement** (rail-optimized topology, rank-to-rail mapping) | Most traffic never reaches the spine, so ECMP is not consulted | Depends on scheduler and NCCL topology choices; cross-rail traffic still exists |
| **Adaptive routing / packet spraying** with selective-repeat NICs | Per-packet or per-flowlet path choice by queue load | Vendor-specific; requires reorder tolerance (go-back-N NICs would retransmit heavily) |
| Hashing on BTH fields (destination QP) | More entropy from the same flows | ASIC support varies |

## Common mistakes

"Add more spines": wider ECMP does not fix too few flows. Blaming "noisy hardware" without the hash
mechanism.
