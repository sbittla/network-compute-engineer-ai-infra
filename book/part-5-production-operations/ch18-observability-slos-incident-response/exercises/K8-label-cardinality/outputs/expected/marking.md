# Marking scheme: K8 Label cardinality for per-rank, per-step metrics

Type knowledge-check · kind computed · tier L1 · 5 points

**Evidence required:** The series-count calculation and where that information should live instead.

| Criterion | Points |
|---|---|
| Reason: each unique label value is a new series; unbounded labels explode memory/index and slow queries | 2 |
| Arithmetic: 86,400 / 17.4 ≈ 4,966 steps/day × 4,096 ranks ≈ 20.3 million series per day | 2 |
| Correct home: logs or trace/flight-recorder store; export only aggregates (histogram by job_id) | 1 |
