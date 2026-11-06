# 8.7 — Lossless two ways: credits and PFC (worked solution)

Relies on manuscript Section 8.5 ("Partitions, service levels, and credit-based flow control"), Section
8.4 (the NIC↔switch data path) and the Chapter 9 headroom formula (Section 9.4).

## InfiniBand: credit-based flow control

The receiver of each link **advertises free buffer space per virtual lane (VL)** in flow-control
packets, counted in 64-byte credits. The sender may transmit a packet on a VL only if it holds enough
credits for it, and it spends credits as it sends. It **never sends a packet without guaranteed buffer
at the far end**, so the receiver buffer cannot overflow. Congestion turns into the sender *waiting*.

## Ethernet: priority flow control (PFC, IEEE 802.1Qbb)

The receiver watches its ingress buffer per priority. When occupancy crosses the **XOFF** threshold it
sends a **pause frame** for that priority (for example priority 3 on ORION) telling the upstream
transmitter to stop. When occupancy falls below XON it sends a resume (pause with quanta 0) or lets
the timer expire.

## Why PFC needs headroom and credits do not

PFC is *reactive*. Between the receiver deciding to pause and the sender actually stopping, bytes keep
arriving: the pause frame's own propagation, the sender's response time and the frame it is already
transmitting, plus the bytes already on the cable. The receiver must reserve **headroom** above XOFF for
these bytes, about 2 × MTU + 2 × rate × cable delay + rate × response time + the pause frame (Chapter 9:
≈ 118 KB for a 100 m, 400 Gb/s link `[MODELED]`). If headroom is short, the "lossless" class drops
packets. Credits are *proactive*: the sender transmits only into buffer that has already been granted,
so nothing is ever "in flight beyond the limit". No headroom is required beyond covering the
round-trip time of credit return for full throughput.

## Back-pressure counters

| Fabric | Counter | Where |
|---|---|---|
| InfiniBand | **`PortXmitWait`**: ticks during which the port had data to send but no credits | `perfquery` on the HCA or switch port |
| Ethernet / RoCE | **Per-priority pause counters** on the NIC: `rx_prio3_pause` / `tx_prio3_pause` (mlx5 names via `ethtool -S`, `[VENDOR-SPEC, 2026-10]`), plus pause-duration counters | Host NIC |
| Ethernet / RoCE | Switch **PFC tx/rx counters per priority** and the per-priority queue/PG watermark | Switch CLI or telemetry |

Direction matters: a high *rx* pause count means "my peer is asking me to stop"; a high *tx* count
means "my buffer is filling".

## Common mistakes

"IB never congests": it back-pressures, and congestion trees exist there too. Saying credits are sent
per packet: they are per buffer block per VL. Naming generic interface "drops" as the PFC counter.
