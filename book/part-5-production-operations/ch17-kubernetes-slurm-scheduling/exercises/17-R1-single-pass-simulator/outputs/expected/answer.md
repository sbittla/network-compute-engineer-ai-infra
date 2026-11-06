# 17-R1 — What a single-pass simulator hides

The lab simulator attempts each job once, against a frozen snapshot, in priority/share/age order.
Real schedulers do more (any two, each with a job effect):

1. **Backfill with reservations.** Slurm's backfill scheduler reserves resources for the
   highest-priority pending job using job time limits, and lets lower jobs start only if they do not
   delay it. J01 (32 GPUs, InsufficientCapacity) would get a reservation on the next four whole
   nodes; J08 might then be blocked from n13 + n18 if its time limit overlapped the reserved start.
2. **Time.** Running jobs end: R-pt-002 finishing frees n09–n12 (32 GPUs, rack-03) and J01 starts
   there; the single pass reports J01 pending forever.
3. **Preemption.** J10 (priority 100) could preempt best-effort work instead of fitting into free
   GPUs; a `requeue` QOS would make J06's best-effort placement revocable.
4. **Quota borrowing (Kueue cohorts).** J14 could borrow idle quota within its cohort instead of
   QuotaExceeded (inference 42 + 8 = 50 > 48 nominal).
5. **Repeated scheduling cycles and retries**: a job rejected for Fragmentation in one cycle can
   start in the next when a small job ends.

Effect on Table 17.7: with (1) and (2), J01's "InsufficientCapacity" becomes a finite wait; with (4),
J14 moves from QuotaExceeded to placed. A credible report says which effects the single pass ignores
before drawing policy conclusions. Source: Sections 17.4, 17.9 Step 7.
