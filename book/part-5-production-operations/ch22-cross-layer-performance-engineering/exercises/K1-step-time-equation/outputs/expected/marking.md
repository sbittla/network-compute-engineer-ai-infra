# Marking scheme: K1 Step-time equation and evidence sources

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** the equation with all six terms; one named tool or metric per term with its grain.

| Criterion | Points |
|---|---|
| Equation with all six terms (compute, exposed comm, bubble, exposed data, host, amortized checkpoint) | 2 |
| T_comm,exposed: a direct overlap-aware source (Nsight Systems NCCL ranges or framework collective-wait timer) with its grain | 1 |
| T_data,exposed: the loop timer around next(iterator) (data_wait per step) with its grain | 1 |
