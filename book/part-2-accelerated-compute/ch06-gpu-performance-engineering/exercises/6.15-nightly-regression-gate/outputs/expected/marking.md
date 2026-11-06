# Marking scheme: 6.15 Nightly performance-regression gate

Type design-challenge · kind computed · tier L1 · 10 points

**Evidence required:** a design with budget arithmetic, the decision rule, and the rejected alternative.

| Criterion | Points |
|---|---|
| Budget arithmetic: workloads fit 16 GPU-hours (e.g. 2 nodes × 8 GPUs × 1 h) | 2 |
| Node selection and stratification (same-node history, reference node) | 2 |
| Decision rule (permutation p < 0.05 and regression > max(A/A floor, 2 %) blocks; warn band) | 2 |
| A/A floor control under 1 % (dedicated nodes, persistence, warm-up, pinned containers, interleaving) | 2 |
| Rejected alternative defended (e.g. running on whichever production nodes are free) | 2 |
