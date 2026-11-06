# Marking scheme: T1 Lossless discards on one uplink

Type troubleshooting · kind computed · tier L1 · 15 points

**Evidence required:** ranked hypotheses with the evidence that discriminates them; two headroom values and the deficit with arithmetic; the eth1/33 headroom calculation and an explicit statement of what the evidence can and cannot prove about it; fix with change-control steps and validation criteria.

| Criterion | Points |
|---|---|
| (a) ≥ 3 ranked hypotheses; undersized headroom on the 100 m uplink first, with the discriminating evidence | 4 |
| (b) Provided 70,996 B (5 m), needed 118,496 B (100 m), deficit 47,500 B with arithmetic | 4 |
| (c) eth1/33 needs 78,496 B (7,500 B short); states that zero discards cannot prove it safe | 3 |
| (d) Fix via change pipeline (canary, rollback, Fabric approval) and validation (0 TC 3 discards ≥ 24 h, fleet audit) | 4 |
