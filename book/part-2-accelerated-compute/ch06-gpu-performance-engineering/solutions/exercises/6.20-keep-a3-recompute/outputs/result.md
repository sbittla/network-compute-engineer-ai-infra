# Exercise 6.20 — C vs A with and without the version rule

Run A3 (PyTorch 2.3.1) median is -2.7 % vs the other baseline runs.

| Protocol | Baseline runs | Change | 95 % band | Permutation p | Decision |
|---|---|---|---|---|---|
| version rule (A3 excluded) | 5 | -0.50 % | [-0.82 %, +0.18 %] | 0.026 | below_threshold |
| no version rule (A3 kept) | 6 | -0.44 % | [-0.77 %, +1.19 %] | 0.994 | not_significant |
