# R3 — What changes if failed jobs are excluded (solution)

The only failed job is 41114 (TP-split, NCCL timeout, 60 usable steps). `solve.py` refits the lab model
without it `[SIMULATED]`.

**Conclusions that change (in size):**

| Quantity | All 48 jobs | Without 41114 |
|---|---|---|
| Headline mean change | +23.2 % | +21.9 % |
| TP-split share | 64.7 % | 61.4 % |
| Common-shift share | 8.3 % | 8.9 % |
| Driver share | 11.2 % | 12.4 % |

Excluding the failed job removes one of the seven TP-split jobs, the factor that caused the failure, so
the placement change looks smaller and the other shares inflate to fill 100 %. Statements about tails and
breadth also weaken: per-job p99 summaries lose their worst job, and "7 of 24 after-period jobs were
TP-split" becomes 6 of 23.

**Conclusions that do not change:**

- The *ranking* of causes: TP split ≫ capacity tier > driver > common shift.
- The ECC-alert verdict: its effect stays within noise (|effect| < 2 SE), ruled out.
- The storage cross-check: the direct data-wait delta of TP-packed jobs (+1.46 s) is untouched by
  removing a TP-split job and still agrees with the storage coefficient within 0.3 s.

**Why it matters.** The direction of the bias is predictable: excluding failures understates the very
regression that produced them (survivorship bias, Section 22.8). Report failures separately *and* keep
their usable steps; if cost is the concern, use the step-weighted change (+22.3 %), which down-weights
the short job transparently.

**Common wrong answers.** "Nothing changes because it is only one job"; claiming the ranking changes;
excluding the job and not saying so.
