# K4 — Why plan to 85 %? Worked solution

Source: manuscript Section 21.3 ("Forecasting demand"), with Chapter 17 for gang scheduling.

**Queueing argument.** A shared cluster is a queue: jobs arrive at random and hold GPUs for random
durations. In any such queue the expected waiting time grows non-linearly with utilization ρ. For the
simplest single-server model it scales as ρ / (1 − ρ): ≈ 5.7 job-times at ρ = 0.85, 19 at 0.95, and
unbounded as ρ → 1 `[MODELED]`. Multi-server queues are flatter at moderate load but show the same
wall near 100 %. Planning demand = 100 % of usable capacity therefore plans for unbounded queues.
Planning to 85 % (required = demand / 0.85, so 420 GPUs of demand need 494.1 usable) keeps waits
bounded and leaves slack for failures. With the canonical 1,536 h node MTBF, ORION-XL loses ≈ 8 nodes
per day (Chapter 19), so the slack is used.

**Consequence for gang-scheduled jobs.** A gang job needs all its nodes at once, often whole leaf
groups. At high average allocation, free capacity exists only as scattered 1–6 node fragments
(Section 21.11: the head-of-queue 4-node job waited with 44 GPUs free but only 2 whole nodes). A
large job waits until enough running jobs end *in the same topology block*, which takes far longer
than the average utilization suggests. Large jobs starve while small jobs backfill, so the cluster
looks busy and the most important work does not run. The scheduler can drain a block in advance
(reservations), but the drained GPUs are idle while it waits; that idle time is the headroom being
paid for anyway.

**Marking notes.** Full marks need both parts: the non-linear queueing argument, and the
contiguity/gang effect. "Leave room for growth" alone earns 1 point.

**Common wrong answer.** "85 % because 15 % of nodes are broken". Failures and maintenance are
already removed in the *usable* fraction (Section 21.2). The 85 % is a separate allocation target for
queueing headroom.
