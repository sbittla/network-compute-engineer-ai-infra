# Marking scheme: 8.7 Lossless two ways: credits and PFC

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** mechanism of each; headroom reasoning; `PortXmitWait` and per-priority pause counters named.

| Criterion | Points |
|---|---|
| IB credit-based flow control: receiver advertises per-VL buffer credits; sender never transmits without credit | 1 |
| PFC: receiver sends per-priority pause at XOFF; in-flight data keeps arriving | 1 |
| Headroom reasoning: PFC needs headroom for bytes in flight after the pause decision; credits do not | 1 |
| PortXmitWait named as the IB back-pressure counter | 1 |
| Per-priority pause counters named (NIC ethtool -S rx/tx_prio3_pause, switch PFC tx/rx per priority) | 1 |
