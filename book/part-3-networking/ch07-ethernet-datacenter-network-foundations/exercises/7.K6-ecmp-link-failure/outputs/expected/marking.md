# Marking scheme: 7.K6 ECMP-aware ingress after one link failure

Type knowledge-check · kind computed · tier L1 · 3 points

**Evidence required:** both numbers with arithmetic and the one-sentence mechanism.

| Criterion | Points |
|---|---|
| Raw uplink 31 × 400 = 12,400 Gb/s, −3.1 % | 1 |
| ECMP-aware ingress 4 × 7 × 400 = 11,200 Gb/s, −12.5 % | 1 |
| Mechanism: unweighted ECMP still sends a quarter of the traffic via the weakened spine, which has only 7 links | 1 |
