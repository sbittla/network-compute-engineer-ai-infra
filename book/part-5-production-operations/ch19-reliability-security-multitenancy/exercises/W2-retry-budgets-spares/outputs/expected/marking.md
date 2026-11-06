# Marking scheme: W2 Retry budgets and spares

Type worked-problem · kind computed · tier L1 · 12 points

**Evidence required:** arithmetic for each part; a recommendation with its trade-off

| Criterion | Points |
|---|---|
| (a) 4.096 µs × 2^20 = 4.295 s per attempt; budget 8 × 4.295 ≈ 34.4 s; all four flaps survived | 3 |
| (b) dead-peer detection 25.8 s later, ≈ 29.3 GPU-h per event vs 683 GPU-h watchdog; flaky link stays in service | 3 |
| (c) 8 failures/day; Poisson means 24 and 40; p99 k = 36 (7.0 %) and k = 55 (10.7 %) | 4 |
| Recommendation with trade-off (ride-through plus flap-rate quarantine; pool is extra capex outside the partition) | 2 |
