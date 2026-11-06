# Marking scheme: 17-T1 21 free GPUs and a pending 8-GPU replica

Type troubleshooting · kind computed · tier L1 · 10 points

**Evidence required:** The GPU reconciliation arithmetic, ranked hypothesis table, root cause, safe fix, validation, and one prohibited action with the reason.

| Criterion | Points |
|---|---|
| Reconciliation: 27 allocated = quota; 21 = n26 4 + n27 5 + n29 4 + n31 8; 37 physically idle incl. n28 and n30 | 3 |
| Ranked hypothesis table (≥ 4) with discriminating commands and verdicts | 3 |
| Actionable root cause (device plugin CrashLoopBackOff on n30 after driver canary) vs by-design causes | 2 |
| Safe fix with validation, plus one prohibited action with reason | 2 |
