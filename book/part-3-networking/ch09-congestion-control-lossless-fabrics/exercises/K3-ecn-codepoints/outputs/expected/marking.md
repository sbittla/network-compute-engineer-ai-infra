# Marking scheme: K3 ECN codepoints and WRED

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** four bit patterns; two behaviours; one reason.

| Criterion | Points |
|---|---|
| Four bit patterns: Not-ECT 00, ECT(1) 01, ECT(0) 10, CE 11 | 2 |
| Above Kmin an ECT packet is marked CE with probability p(q) | 1 |
| Above Kmin a Not-ECT packet is dropped with the WRED probability | 1 |
| Reason: a drop in lossless TC 3 triggers go-back-N; RoCE data must be ECT and WRED drop disabled | 1 |
