# Exercise 6.13 — is the improvement real?

Baseline median = 12.425 ms. Decision bar = max(0.9 %, 2 %) = 2 %; α = 0.05.

| Candidate runs | Median | Change | 95 % bootstrap band | Exact permutation p | Decision |
|---|---|---|---|---|---|
| all_runs (6) | 12.170 ms | -2.05 % | [-2.97 %, +1.65 %] | 0.361 | not_significant |
| without_run5 (5) | 12.120 ms | -2.45 % | [-3.16 %, -0.85 %] | 0.002 | improvement |
