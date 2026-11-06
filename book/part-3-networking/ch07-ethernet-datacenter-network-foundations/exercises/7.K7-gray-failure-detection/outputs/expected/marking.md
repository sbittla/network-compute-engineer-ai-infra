# Marking scheme: 7.K7 Gray failures and detection time

Type knowledge-check · kind computed · tier L1 · 3 points

**Evidence required:** definition, mechanism, two detection times.

| Criterion | Points |
|---|---|
| Definition: component looks up (link up, control plane alive) but does not forward correctly | 1 |
| BFD named as the mechanism that catches it | 1 |
| Both detection times: 300 ms × 3 = 0.9 s (BFD) and up to 9 s (BGP 3 s / 9 s hold) | 1 |
