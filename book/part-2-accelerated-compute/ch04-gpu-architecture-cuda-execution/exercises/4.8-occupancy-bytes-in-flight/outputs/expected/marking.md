# Marking scheme: 4.8 Occupancy and bytes in flight

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** every limit computed, limiter named, bandwidth bound with arithmetic.

| Criterion | Points |
|---|---|
| (a) all four limits computed (warps 16, registers 6, shared memory 4 with the 1 KB reservation, blocks 32); 25 % occupancy, limiter shared memory | 4 |
| (b) 15,227 B needed per SM; 4,096 B in flight; 26.9 % of HBM, about 0.90 TB/s upper bound, labelled [MODELED] | 3 |
| (c) shared memory 6 blocks, registers 6; 37.5 % occupancy, limiter registers (tie with shared memory accepted); 40.3 %, about 1.35 TB/s | 3 |
