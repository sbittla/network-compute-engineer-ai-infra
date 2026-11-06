# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `load_telemetry` | PASS load_telemetry: rows=3840 ranks=64 steps=60 |
| `per_step_stats` | PASS per_step_stats: step 10: slowest rank 12, ratio 1.294 (exp 1.294) |
| `robust_z` | PASS robust_z: z(rank 37, step 40) = 14.4 (exp 14.4) |
| `find_stragglers` | PASS find_stragglers: stragglers=[12, 37] (expect two ranks with persistent robust z > 6) |
| `rank_onset` | PASS rank_onset: onset rank 37 = 20, rank 12 = 0 |
| `attribute_cause` | PASS attribute_cause: rank 37 -> thermal, rank 12 -> data_imbalance |
| `rail_health` | PASS rail_health: flagged rails=[2], onset=[30.0] |
| `hot_not_throttled` | PASS hot_not_throttled: hot-but-not-throttled=[51] |
| `amplification` | PASS amplification: lost 334 GPU-s (17.3 %), ideal step 827 ms vs actual 1004 ms |
| `symptom_windows` | PASS symptom_windows: sm_active 58.5 -> 54.7 %, gpu_util 99.7 -> 99.7 %, comm 120 -> 198 ms, burst tx 359 -> 222 Gb/s |
| `missing_samples` | PASS missing_samples: 200 rows dropped, 37 NaN: stragglers=[12, 37], onset rank 37 = 20 (expect [12, 37], 20-22) |
