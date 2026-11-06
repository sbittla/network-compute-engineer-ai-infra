# Marking scheme: 14.13 Checkpoint strategy for ORION-XL

Type design-challenge · kind computed · tier L1 · 15 points

**Evidence required:** the YAML you used, the planner table, a capacity calculation, and a one-page defended recommendation

| Criterion | Points |
|---|---|
| YAML changes and planner table (async PFS 180 s/9 steps 9,927 GPU-h/day; other rows) | 4 |
| Capacity and retention: 5.67 TB per checkpoint, at most 4 in 25 TB (3 validated + 1 in flight), archive policy | 3 |
| RPO (≤ 5 min, achieved 202 s) and RTO (15 min, expected 905 s) targets | 3 |
| Tenant burst: 5.67 TB in 18.9 s every 180 s, ≈ 12 % duty, 7.9 % of write capacity; mitigation | 2 |
| Highest-leverage improvement: time-to-resume (detection 300 to 60 s saves ≈ 2,185 GPU-h/day) | 3 |
