# Marking scheme: D1 Continuous regression detection for ORION

Type design-challenge · kind computed · tier L1 · 15 points

**Evidence required:** architecture sketch; a trade-off table with at least two options and four criteria (detection time, GPU cost, false-positive rate, causal strength); a stated recommendation with the arithmetic for canary cost and detectable effect.

| Criterion | Points |
|---|---|
| Architecture sketch with data sources (step logs, placement, time-aware inventory, change calendar) and the attribution stage | 3 |
| Trade-off table: at least two options against the four criteria | 4 |
| Canary GPU cost arithmetic (64 GPU-h/day of 6,144 = 1.04 %) | 3 |
| Detectability arithmetic (3 % of 17.4 s = 0.52 s; n = 0.70) and threshold baseline + max(3σ, 3 %) | 3 |
| Recommendation justified against false-positive cost and causal strength | 2 |
