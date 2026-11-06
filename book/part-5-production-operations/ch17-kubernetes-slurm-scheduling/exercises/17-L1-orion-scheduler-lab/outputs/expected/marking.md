# Marking scheme: 17-L1 Lab 17: ORION scheduler simulator and diagnoser

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** `python check.py` output showing `10/10 checks passed`; the two reports per the lab rubric. For an L2/L3 extension, the filled-in copy of `manifest.yaml` and the captured events or `all_reduce_perf` results (≥ 5 repetitions, median and p95).

| Criterion | Points |
|---|---|
| Tasks 1–3: tolerates, node_filter, select_gpus (T1, T2, T3 pass) | 28 |
| Task 4: place_job single-node and gang (both T4 lines pass) | 17 |
| Task 5: schedule invariants, exact match, order/fairness (T5 pass) | 20 |
| Task 6: diagnose_pending 12/12 (T6 pass) | 15 |
| Task 7: placement-report.md — five pending jobs with reasons, J01 capacity-blocked after J05 (not fair share), rail and lifecycle effects, one policy change | 10 |
| Task 8: pending-guide.md — each code mapped to real kubectl/Slurm commands and a safe fix with a 'do not' | 10 |
