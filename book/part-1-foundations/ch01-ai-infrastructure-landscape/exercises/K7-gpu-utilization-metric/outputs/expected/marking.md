# Marking scheme: K7 Why GPU utilization is weak evidence

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** The mechanism and a better metric.

| Criterion | Points |
|---|---|
| Explains that GPU utilization is the fraction of time any kernel is running, including communication kernels waiting on peers | 2 |
| Names DCGM_FI_PROF_SM_ACTIVE or DCGM_FI_PROF_PIPE_TENSOR_ACTIVE (or their DCGM 4.6+ ratio names) as a better metric | 1 |
| Gives an example where utilization stays high while useful work falls | 1 |
