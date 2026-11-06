# Marking scheme: Q1 GPU utilization 97 % as evidence

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** The mechanism and a better metric.

| Criterion | Points |
|---|---|
| Utilization counts any running kernel, so communication kernels waiting on peers count as busy | 1 |
| Names SM-active or tensor-active (DCGM profiling fields) as the better metric | 1 |
| Links to the Section 1.11 incident or an equivalent example of high utilization with low useful work | 1 |
