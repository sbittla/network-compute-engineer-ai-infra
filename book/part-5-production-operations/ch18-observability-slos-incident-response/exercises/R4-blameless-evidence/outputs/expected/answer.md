# R4 — What makes a postmortem blameless

**Evidence in the document that it is blameless** (Section 18.11, Table 18.8b):
- It describes *system conditions and decisions in context*: what the person knew, what the tooling
  showed, which defaults and gates applied, so that the same action would be reasonable for anyone.
- No names attached to errors; roles appear only as owners of action items.
- Root cause is a set of *contributing factors* (no performance canary for QoS changes, fleet-wide
  rather than rail-by-rail rollout, no training-SLO alert), not "human error".
- Action items change systems (alerts, gates, rollback tooling) and each has an owner, priority, due
  date, and type (detect / mitigate / prevent).
- The timeline is built from machine evidence first (`events.jsonl`, `job_steps.csv`), and
  "where we got lucky" is recorded honestly.

**Rewrite example.**
- Blaming: "The network engineer pushed a bad config and broke training."
- Blameless: "CHG-4471 applied buffer-profile v2 to all eight rail leaves within four minutes. Its
  post-checks verified interfaces, BGP, and discards but not RoCE performance, so the regression
  passed the change gate; no alert covered training throughput, so detection depended on a researcher
  noticing 48 minutes later."
- Second example: "On-call ignored the problem" → "The only page-severity GPU rule (`GPUUtilLow`)
  measures time-occupancy, which stays ≈ 97 % while NCCL kernels wait on the network; it paged 63
  times on idle inference nodes and never for this incident."
