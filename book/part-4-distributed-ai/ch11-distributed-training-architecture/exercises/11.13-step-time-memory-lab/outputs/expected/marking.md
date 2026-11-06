# Marking scheme: 11.13 Step-time and memory model (lab)

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** checker output (10/10 PASS), candidate table, recommendation with justification, checkpoint table, and a paragraph on the planted traps.

| Criterion | Points |
|---|---|
| bubble_fraction, validate_config and memory checks pass (memory_baseline, memory_traps) | 30 |
| allreduce_time, comm_volumes_baseline and step_time_baseline pass | 30 |
| evaluate_and_recommend passes and the recommendation (D_tp4_pp8_dp8) is justified on step, MFU and headroom | 15 |
| young_daly and reliability_table pass; checkpoint table in the report | 15 |
| Planted traps explained (G and I overflow, J violates headroom, E spans nodes and breaks KV-head divisibility, K full recompute is slower) | 10 |
