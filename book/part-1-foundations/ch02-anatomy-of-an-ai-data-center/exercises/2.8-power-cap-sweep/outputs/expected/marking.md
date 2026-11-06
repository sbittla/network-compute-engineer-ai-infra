# Marking scheme: 2.8 Power-cap sweep on one GPU server

Type hands-on-lab · kind written · tier L2 · 20 points

**Evidence required:** Filled-in lab/manifest.yaml copy (GPU model, driver, default limit, workload definition, warm-up, repetitions); raw CSV; plot; median and spread per step; explicit [MEASURED] versus [MODELED] labels for the answer to question 3.

| Criterion | Points |
|---|---|
| Manifest and benchmark discipline (2-minute warm-up, 5 repetitions, median and spread per step, defaults restored and recorded) | 8 |
| Plots of throughput, average power and throughput per watt against the limit | 4 |
| Correct interpretation of compute-bound versus memory-bound curves | 4 |
| Question 3 picks the 570 W feed-loss limit (or the highest limit that meets the feed-loss budget) and converts it to a W-TRAIN step-time impact labelled [MODELED from MEASURED] | 4 |
