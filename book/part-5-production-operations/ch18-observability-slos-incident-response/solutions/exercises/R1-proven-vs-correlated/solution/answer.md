# R1 — Proven versus correlated in the lab postmortem

**Proven by the bundle** `[SIMULATED]`:
- *Temporal precedence:* CHG-4471's leaf changes (02:08–02:12, `events.jsonl`) precede the onset at
  02:10 in `job_steps.csv`; nothing else changed in that window except monitoring (CHG-4468, 01:30).
- *Scope:* both jobs regressed at the same minute on disjoint node sets (orion-n01..n16 and
  n17..n24); their only shared resources are the backend fabric, storage, and schedulers; inference
  (no per-request backend traffic) was unaffected (`inference_slo.csv`).
- *Intervention:* the rollback CHG-4471-RB (04:02–04:08) is followed by recovery at 04:07 and PFC/ECN
  back in band (`switch_metrics.csv`). An intervention that removes the symptom is the strongest
  evidence the bundle holds.

**Only correlated:** the *mechanism*: that raised ECN/WRED thresholds let queues reach PFC XOFF before
DCQCN reacted. The bundle shows leaf PFC TX × 91–98 and ECN × 0.03 per minute per switch (Table
18.9), consistent with that story, but has no queue-depth or per-queue telemetry to show the order of
events inside a queue. Spine PFC RX × ≈ 105 is propagation, not origin.

**Evidence that would make it proof:** per-queue buffer watermarks and per-port, per-priority pause
durations at 1–10 s resolution; DCQCN counters (`np_cnp_sent`, `rp_cnp_handled`) per host; and a
controlled reapplication of the profile on a single rail leaf in a lab (or a canary leaf behind an
`all_reduce_perf` gate) showing the regression appears and disappears with the change.
Source: Section 18.12 Steps 7–9; lab marking guidance for Task 4.
