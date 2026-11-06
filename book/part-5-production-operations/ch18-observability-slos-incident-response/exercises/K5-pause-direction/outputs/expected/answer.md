# K5 — Who is pausing whom?

Counter semantics (`ethtool -S`, mlx5, priority 3 = ORION's lossless RoCE class):
`rx_prio3_pause` counts pause frames *received* by the host; `tx_prio3_pause` counts pause frames the
host *sent*.

| Host | Counter rising | Who pauses whom | Bottleneck | Role |
|---|---|---|---|---|
| A | `rx_prio3_pause` | The switch is pausing **this host's transmissions** on the lossless class | Downstream: switch egress congestion (incast toward some receiver) or a slow receiver elsewhere that is back-pressuring the switch | **Victim** |
| B | `tx_prio3_pause` | **This host** is pausing the switch: its receive buffers cannot drain | Host-side: PCIe (degraded width, ACS/IOMMU), memory bandwidth, slow consumer, receive-queue starvation | **Likely culprit**, spreading back-pressure into the fabric |

**Next checks for host B:** `out_of_buffer` in `rdma statistic` (receive-queue starvation), PCIe link
width and errors (`lspci -vv`), CPU/IRQ placement versus the NIC's NUMA node, `tx_prio3_pause_duration`
growth. For host A: switch-port ECN/PFC counters and queue watermarks along the path to find the
congested egress.

**Common mistake:** reversing the directions; −1 per host reversed. A host that sends pauses can make
many other hosts look like victims (pause propagation, head-of-line blocking), so start from the
sender of pauses. Source: Section 18.4 ("Host-side RDMA counters"); Chapter 9.
