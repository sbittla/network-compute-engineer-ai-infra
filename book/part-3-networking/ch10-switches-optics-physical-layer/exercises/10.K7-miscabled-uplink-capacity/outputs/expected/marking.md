# Marking scheme: 10.K7 Miscabled but error-free uplink

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** ≤ 120 words; name the check that does detect it.

| Criterion | Points |
|---|---|
| Mechanism: each /31 belongs to a specific port pair, so swapped jumpers break eBGP and remove ECMP members | 2 |
| Capacity impact quantified (2 of 32 uplinks = 6.25 % for one swapped pair) | 1 |
| Names LLDP-neighbour-vs-cabling-schedule validation as the detecting check and why physical counters stay at zero | 2 |
