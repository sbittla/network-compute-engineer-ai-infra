# Marking scheme: D1 Hot spares vs elastic training

Type design-challenge · kind computed · tier L1 · 10 points

**Evidence required:** model with assumptions; numeric comparison; recommendation with risks

| Criterion | Points |
|---|---|
| Model with stated assumptions (M = 3 h, τ = 19 min, δ = 1 min, 8 failures/day, mean 40 in repair) | 4 |
| Numbers: A 0.733, B re-packed 0.799, B not re-packed 0.450 expected / 0.325 worst per fleet node | 3 |
| Global-batch divisibility at DP = 59 and recommendation with risks (B only with re-packing; else A or hybrid) | 3 |
