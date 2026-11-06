# Marking scheme: 7.K2 Shared spine ASN, unique leaf ASNs

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** the loop-prevention mechanism in one sentence for each half of the question.

| Criterion | Points |
|---|---|
| Shared spine ASN: AS_PATH loop detection drops any path that already crossed the spine tier (no valley paths, no path hunting) | 2 |
| Duplicate leaf ASN: each leaf drops the other's prefixes because its own ASN is in the AS_PATH | 1 |
| States that the BGP sessions stay Established, so the fault is silent | 1 |
