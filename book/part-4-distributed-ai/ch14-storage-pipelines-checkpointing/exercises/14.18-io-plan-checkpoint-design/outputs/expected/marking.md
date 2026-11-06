# Marking scheme: 14.18 Deliverable: I/O benchmark plan and checkpoint/recovery design

Type deliverable · kind lab · tier L1 · 30 points

**Evidence required:** the document, the planner output it cites, and the validator run on the lab store

| Criterion | Points |
|---|---|
| Benchmark plan: NVMe, PFS bandwidth, PFS metadata (mdtest), read-under-write; exact parameters, warm-up, ≥ 5 reps, percentiles, manifest fields | 8 |
| Checkpoint design: strategy, interval with derivation, staging memory, commit protocol, validation ladder, retention, archive | 8 |
| RPO/RTO analysis: time-to-resume components, lost GPU-h/day, sensitivity to M and detection time | 6 |
| Restore test procedure including a planted corrupt checkpoint and a semantic loss check | 4 |
| Measured vs modeled statement; evidence labels throughout | 4 |
