# Marking scheme: 2.1.6 Is SW Power Cap Active a fault?

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** Verdict with the condition that would make it a fault and the command to check.

| Criterion | Points |
|---|---|
| Not a fault under dense GEMM, because a GPU commonly runs at its power limit | 1 |
| A fault if the current limit is lower than intended, checked with nvidia-smi -q -d POWER (Current vs Default Power Limit) | 1 |
| A fault if only some GPUs in a job are capped (stragglers), or if clocks are far below peers | 1 |
