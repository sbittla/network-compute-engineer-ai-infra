# Exercise 6.20 — C vs A with and without the version rule

Run A3 (PyTorch 2.3.1) median is -2.7 % vs the other baseline runs.

| Protocol | Baseline runs | Change | 95 % band | Permutation p | Decision |
|---|---|---|---|---|---|
| version rule (A3 excluded) | 5 | -0.45 % | [-0.72 %, -0.12 %] | 0.026 | below_threshold |
| no version rule (A3 kept) | 6 | -0.01 % | [-0.65 %, +0.93 %] | 0.994 | not_significant |
