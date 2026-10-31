# 5.9 — Modeled cost of one bad path (model answer)

Relies on manuscript Section 5.9 (the model and Table 5.4). All results `[MODELED]`; parameters
`[ILLUSTRATIVE]`. `solve.py` asserts them.

**Formula.** *t*ᵣ = 2(*n* − 1)/*n* × (*S*/*R*) / min(*b*ᵢ); *t* = maxᵣ *t*ᵣ + α; busbw = 2(*n* − 1)/*n* × *S* / *t*.
With *n* = 256: ring factor = 2 × 255 / 256 = **1.99219**; *S*/*R* = 1,073,741,824 / 8 = **134,217,728 B**, so each
ring moves 1.99219 × 134,217,728 = 267,386,880 B; numerator of busbw = 1.99219 × 1,073,741,824 = 2,139,095,040 B.

| Case | Slowest member | *t* | busbw |
|---|---|---|---|
| (a) all PIX | 48 GB/s | 267,386,880 / 48 × 10⁹ = 5.571 ms + 0.2 = **5.771 ms** | 2,139,095,040 / 5.771 ms = **370.7 GB/s** |
| (b) one NIC on Gen5 x8 | 27 GB/s on one rail's ring | 9.903 + 0.2 = **10.10 ms** | **211.7 GB/s** |
| (c) one node without GDR | 18 GB/s on all eight rings | 14.855 + 0.2 = **15.055 ms** | **142.1 GB/s** |

In (b) only the ring of that NIC's rail is slow, but the collective finishes when its slowest ring does,
so one NIC costs 43 % of busbw.

**(d) Why (c) is worse than "1 of 32 nodes" suggests.** A ring is a synchronous pipeline that passes through
every node and runs at its slowest member's rate. A node without GDR is the slowest member of *all eight*
rings at once, so the whole job runs at the host-staged rate: 142.1 / 370.7 = 38 %, a **62 % loss** from 3.1 %
of the nodes. Averaging over nodes ("31 of 32 healthy → 97 %") is the wrong mental model for collectives;
the right one is the minimum. Operationally: one degraded node must be drained, not tolerated.

**Common wrong answers.** Using 1 GiB per ring (forgetting /*R*); using *n* = 32 nodes instead of 256 ranks;
averaging the slow node into the bandwidth.
