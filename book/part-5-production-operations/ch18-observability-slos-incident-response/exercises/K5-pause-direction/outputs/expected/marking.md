# Marking scheme: K5 Who is pausing whom?

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** Direction of the pause for each host and the likely location of the bottleneck.

| Criterion | Points |
|---|---|
| Host A (rx_prio3_pause rising): receives pauses from the switch; victim; bottleneck downstream in the fabric or a slow receiver elsewhere | 2 |
| Host B (tx_prio3_pause rising): sends pauses because its own receive path cannot drain | 1 |
| Host B identified as likely culprit with a host-side bottleneck location (PCIe, memory, slow consumer, receive buffers) | 1 |
