# 17-R4 — Proving small-job confinement helped

**Claim to test:** "confining small jobs to shared nodes reduced gang queue wait in production."

**Measurement plan.**
- **Primary metric:** multi-node (gang) job queue wait, Submit → Start from `sacct` (or Kueue
  `QuotaReserved`/`Admitted` timestamps), reported as p50 and p95, per gang size class (2, 4, 8+
  nodes).
- **Mechanism metric:** fraction of scheduling cycles in which the largest placeable gang (whole,
  rail-complete, schedulable nodes) ≥ the next queued gang's size; and fragmentation = free GPUs not
  in whole nodes.
- **Guard metric:** small-job queue wait p95 (the policy must not simply move the pain).
- **Window:** ≥ 2 full weeks before and ≥ 2 weeks after the change (weekly submission cycles, Monday
  peaks), excluding the transition days.
- **Comparison:** same job-size mix (stratify or reweight by size class), report job counts per
  class and confidence intervals, not only medians.
- **Confounders:** queue mix changes (a big campaign starting), drains and firmware waves (Chapter
  16), node repairs, quota or priority changes, capacity additions, and holidays. Record them as
  annotations and exclude or adjust.
- **Provenance:** record the policy version in the scheduler manifest so each job's wait is tied to
  the policy that scheduled it.

Without this, a lower wait could come from fewer large submissions or more nodes, not from the
policy. Source: Section 17.6 ("not wasting shape"), Section 17.8 runbook metrics.
