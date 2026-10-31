# W2 — Retry budgets and spares `[MODELED]`

(a) 4.096 µs × 2^20 = 4.295 s; budget = 8 × 4.295 = 34.4 s (was 8.6 s at timeout 18). Flaps [14, 6, 5, 14] s survived: [True, True, True, True]
(b) dead peer reported 25.8 s later: 25.8 s × 4,096 GPUs = 29.3 GPU-h per event (watchdog: 683 GPU-h)
(c) failures/day = 512 × 24 / 1,536 = 8

| MTTR | Mean in repair | p99 pool k | P(X ≤ k) | % of 512 |
|---|---|---|---|---|
| 3 d | 24 | 36 | 0.992 | 7.0 % |
| 5 d | 40 | 55 | 0.990 | 10.7 % |
