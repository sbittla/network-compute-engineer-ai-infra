# Marking scheme: 7.T Half the flows to rail 6 fail after a template push

Type troubleshooting · kind written · tier L1 · 20 points

**Evidence required:** a completed checklist table, ranked hypotheses with the discriminating evidence cited by item number, and a fix/validate/prevent plan with measurable acceptance criteria.

| Criterion | Points |
|---|---|
| (a) Checklist covers the three hypotheses against size, flow, prefix, counters, path trace, BGP view and change history, with what the pack shows | 6 |
| (b) Ranks incorrect advertisement first and explains the 2-of-4 spine split from item 8 (compare-routerid on spines 1 and 3, oldest-path on 2 and 4) | 5 |
| (c) 16 of 32 uplinks lead to spines 1 and 3, so ≈ 50 % of flows fail (31/64 consistent, σ = 4); single pings are hash luck, not a rail property | 3 |
| (d) Rebuts asymmetric routing: normal in ECMP without stateful devices or strict uRPF, and cannot explain prefix-specific loss or the extra origin AS | 2 |
| (e) Safe fix (inbound prefix filter, then template revert, under change control), measurable validation and at least two preventive controls | 4 |
