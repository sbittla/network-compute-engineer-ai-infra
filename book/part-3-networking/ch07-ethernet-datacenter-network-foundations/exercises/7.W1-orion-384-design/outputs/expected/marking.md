# Marking scheme: 7.W1 Design a rail-optimized ORION-384 backend

Type worked-problem · kind computed · tier L1 · 12 points

**Evidence required:** every count with arithmetic; a one-paragraph explanation for (b) and (d).

| Criterion | Points |
|---|---|
| (a) Leaves per rail 2, total leaves 16, spines 8, links per pair 4, with the radix arithmetic | 3 |
| (a) Used/total downlinks 384/512 (75 %), ratio 1:1 as configured and 0.75:1 as used | 1 |
| (a) Cables 384 + 512 = 896 and transceivers 1,792 before spares | 2 |
| (b) Lab result (12 leaves, 8 spines, 768 cables) explained: not rail-aware, 48 NICs per rail = 1.5 leaves | 2 |
| (c) 3:1 variant: 8 leaves, 2 spines, 8 links per pair, 6.4 Tb/s cross-leaf vs 19.2 Tb/s downlink; same-rail stays non-blocking | 3 |
| (d) Same-rail traffic now crosses spines, so ECMP collisions sit on the main collective path | 1 |
