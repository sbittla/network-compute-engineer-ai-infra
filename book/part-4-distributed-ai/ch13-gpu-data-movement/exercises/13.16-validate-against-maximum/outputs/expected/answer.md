# 13.16 — Validating a fix when the maximum sets step time: worked solution

**Implication.** In a synchronous job the step time is max over ranks of (compute + data wait) plus
transfer. In the lab, ranks 12 (data imbalance) and 37 (thermal) are both slow from step 20, so fixing
rank 37 leaves the maximum, rank 12, unchanged. Step time does not move and the fix looks like a failure
even though it worked (Section 13.7).

**How to validate a fix:**

1. **Validate the component, not the job, first.** For rank 37, show that its own compute time returns
   to the peer median (robust z < 6), its SM clock matches peers, and no clocks-event reason is set.
   These per-rank measurements prove the thermal fix independently of rank 12.
2. **Validate the job against the ideal.** Compute the ideal step, with every rank at the median
   compute (827 ms in the lab), and track actual versus ideal. A job-level fix is complete only when
   *all* stragglers are fixed and the gap closes (1,004 → about 827 ms, and transfer back to 120 ms
   once rail 2 is repaired) `[SIMULATED]`.
3. **Order by amplification.** Prioritize the fix that changes the maximum. Communicate that the
   others give no step-time gain until the dominant one is fixed, so nobody reverts a correct fix.
4. **Look at distributions.** Compare wait-time distributions on the other ranks before and after.
   Waits attributable to rank 37 disappear even when the maximum does not move.

A step-time-only acceptance test can reject a correct fix or accept a coincidence.
