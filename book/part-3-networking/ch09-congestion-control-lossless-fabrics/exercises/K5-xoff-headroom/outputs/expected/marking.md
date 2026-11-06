# Marking scheme: K5 Xoff threshold versus headroom

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** two definitions; symptom naming a specific counter; reason tied to the formula.

| Criterion | Points |
|---|---|
| Xoff defined: ingress PG occupancy at which pause is sent | 1 |
| Headroom defined: separate per (port, lossless PG) reservation absorbing bytes that arrive after the decision | 1 |
| Symptom: non-zero lossless-class discards (discards_tc3) despite active PFC | 1 |
| Longest links first because the 2 × r × L / v term grows with cable length | 1 |
