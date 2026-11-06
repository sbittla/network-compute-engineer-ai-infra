# 13.12 — Cross-layer straggler diagnosis (lab): worked solution

**Checker.** `python lab/check.py` must report **11/11 checks passed**. The reference report
(`solutions/lab/outputs/check_solution.txt`) gives `[SIMULATED]`:

```text
find_stragglers: stragglers=[12, 37]
rank_onset: onset rank 37 = 20, rank 12 = 0
attribute_cause: rank 37 -> thermal, rank 12 -> data_imbalance
rail_health: flagged rails=[2], onset=[30.0]
hot_not_throttled: hot-but-not-throttled=[51]
amplification: lost 334 GPU-s (17.3 %), ideal step 827 ms vs actual 1004 ms
missing_samples: 200 rows dropped, 37 NaN: stragglers=[12, 37], onset rank 37 = 20
symptom_windows: sm_active 58.5 -> 54.7 %, gpu_util 99.7 -> 99.7 %, comm 120 -> 198 ms, burst tx 359 -> 222 Gb/s
```

**Findings table.**

| Cause | Ranks | Onset | Evidence | Owner | Fix | Validation |
|---|---|---|---|---|---|---|
| Data imbalance | 12 | step 0 | compute z ≫ 6; tokens +31 %; clocks, temperature and power normal | Training Infra / data | rebalance the shard or pack sequences by tokens | rank 12 tokens within ±5 % of median; wait time on others < 20 ms |
| Thermal throttle | 37 | step 20 | SM clock −22 %, 90 °C, `sw_thermal_slowdown`; tokens normal | Fleet (facilities) | inspect airflow/fans; drain the node if it persists | clocks at peer median under load; no throttle reason over 1 h |
| Rail 2 degradation | local index 2 on all 8 nodes | step 30 | retransmissions ≈ 3,200 per step vs ≈ 1; transfer 120 → 198 ms; burst 359 → 222 Gb/s | Network | inspect `orion-be-leaf-r2` (recent change, optics, FEC) | retransmissions ≈ baseline; transfer back to ≈ 120 ms |
| Decoy | 51 | — | 84 °C, normal clocks, no reason | — | none | — |

**Amplification.** Steps 30–59 lose 334 GPU-s, 17.3 % of GPU time. The ideal step is 827 ms against an
actual 1,004 ms. Fixing rank 37 alone does not move the step time, because rank 12 still sets the
maximum (Section 13.7). A fix is validated against the step-time maximum, not per rank.

**Diagram.** Attach the 13.9 data-path diagram annotated with where each fault sits: rank 12 at the
data loader, rank 37 at the GPU, and rail 2 at `orion-be-leaf-r2` between NIC 2 and NIC 2.

Reference implementation: `solutions/lab/telemetry_diag.py`. Notes: `solutions/lab/README.md`.
