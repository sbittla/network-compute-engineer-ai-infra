# Marking scheme: 4.5 What nvidia-smi GPU-Util measures

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** definition, example with numbers, two field names with meanings.

| Criterion | Points |
|---|---|
| Definition: percent of the sample period during which one or more kernels was executing (a duty cycle, not SM efficiency) | 2 |
| Numeric example where GPU-Util reads 100 % but delivered throughput is below 5 % of peak (for example 4-block kernels on 4 of 132 SMs = 3 %) | 1 |
| Two DCGM profiling fields named with correct meanings (for example DCGM_FI_PROF_SM_ACTIVE, DCGM_FI_PROF_PIPE_TENSOR_ACTIVE) | 2 |
