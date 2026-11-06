# Marking scheme: 7.W2 Failure capacity of ORION-384

Type worked-problem · kind computed · tier L1 · 12 points

**Evidence required:** a results table, formulas with substituted values, and a 3–5 sentence comparison.

| Criterion | Points |
|---|---|
| (a) Baseline row: 12.8 / 12.8 / 102.4 Tb/s | 2 |
| (a) One link down: 12.4 / 9.6 / 102.0 Tb/s, with the 8 × 3 × 0.4 ingress arithmetic | 2 |
| (a) One spine down: 11.2 / 11.2 / 89.6 Tb/s | 2 |
| (b) Link penalty 25 % vs 12.5 % on ORION-256, explained by 4 vs 8 links per bundle under unweighted ECMP; spine penalty reverses | 3 |
| (c) P(no collision) = 4!/4⁴ = 9.4 % and expected links used = 4 × (1 − (3/4)⁴) = 2.73 | 3 |
