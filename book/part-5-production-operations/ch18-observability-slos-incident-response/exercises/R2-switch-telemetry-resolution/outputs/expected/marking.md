# Marking scheme: R2 What one-minute switch aggregates cannot show

Type reflection · kind written · tier L1 · 5 points

**Evidence required:** Concise written answers, each referencing a specific data file, metric, or section.

| Criterion | Points |
|---|---|
| Names what one-minute per-switch aggregates hide (which ports/queues paused, microbursts, pause storms/ordering) | 2 |
| Explains why (averaging dilutes ms-scale events; per-switch sums hide port locality) | 1 |
| Telemetry to add: per-port per-priority pause duration, queue watermarks, ECN marks at 1–10 s via gNMI | 2 |
