# Marking scheme: 7.K3 MTU mismatch and the eBGP session

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** the role of the TCP MSS; the direction(s) in which large frames are lost.

| Criterion | Points |
|---|---|
| TCP MSS mechanism: each side advertises an MSS from its own MTU and the peer never exceeds it, so BGP segments are ≤ 1,460 B | 2 |
| 9216 → 1500 direction: oversize frames dropped at ingress (giants), silently | 1 |
| 1500 → 9216 direction: packets routed out of the 1500 interface fail the egress MTU check; concludes loss in both directions | 1 |
