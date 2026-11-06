# Marking scheme: 8.16 ORION-XL fabric policy

Type design-challenge · kind computed · tier L1 · 20 points

**Evidence required:** decision with criteria; every parameter with its number and label; one quantified trade-off; one risk you are accepting and how you would detect it in production.

| Criterion | Points |
|---|---|
| Decision (RoCEv2 or InfiniBand) with explicit criteria and loss model | 5 |
| Parameters with numbers and labels: 3-tier RTT and BDP, timeout/retry with time-to-failure, MTU, GID policy | 6 |
| One quantified trade-off (e.g. tail-loss cost at the design loss rate vs spurious-failure cost) | 4 |
| An accepted risk and how it is detected in production | 3 |
| Scale considerations for the readiness checklist at 512 nodes and single-NIC failure handling | 2 |
