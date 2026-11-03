# Exercise 6.13 — is the improvement real?

Baseline mean of run medians = 12.4333 ms. Decision bar = max(0.9 %, 2 %) = 2 %; α = 0.05.
Primary statistic: difference in arm means of run medians, % of the baseline mean (change, band and p).

| Candidate runs | Mean | Change | 95 % bootstrap band | Exact permutation p | Decision |
|---|---|---|---|---|---|
| all_runs (6) | 12.2917 ms | -1.14 % | [-2.69 %, +1.14 %] | 0.361 | not_significant |
| without_run5 (5) | 12.1600 ms | -2.20 % | [-2.90 %, -1.42 %] | 0.002 | improvement |

Sensitivity analysis (median of run medians; not the decision):

| Candidate runs | Median | Change | Exact permutation p | Decision if it were used |
|---|---|---|---|---|
| all_runs (6) | 12.170 ms | -2.05 % | 0.041 | improvement |
| without_run5 (5) | 12.120 ms | -2.45 % | 0.013 | improvement |
