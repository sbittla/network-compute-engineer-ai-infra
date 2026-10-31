# R2 — Why a high R² is not evidence of causation (solution)

**What R² measures.** R² = 1 − SS_res / SS_tot is the fraction of variance in per-job mean step time that
the fitted indicators reproduce *in this sample*. It is a statement about fit, not about mechanism.

**Why that is not causation.**

1. **Omitted variables.** Any unmeasured factor correlated with an indicator is absorbed into that
   indicator's coefficient without lowering R². If every TP-split job had also been scheduled onto the
   noisiest racks, the TP coefficient would carry both effects and R² would stay ≈ 0.998.
2. **Direction and selection.** Exposure was not randomized. Users moving away from slow nodes, or
   failed jobs dropped from the population, can create a well-fitting association with the wrong
   direction (Section 22.4.4).
3. **No mechanism.** R² cannot say whether a mechanism exists. Section 22.4 requires three kinds of
   agreement for a cause: the statistical estimate, a direct measurement (for TP split: backend tx 6 → 38
   GB/s, SM active 0.57 → 0.40) and a model of the mechanism (TP all-reduce bytes over inter-node
   bandwidth). R² supplies at most the first.

**The lab's own counterexample** `[SIMULATED]`. The additive-only model (no `tp_x_storage` term) fits with
R² ≈ 0.995, almost as high, yet it reports a "significant" ECC-alert effect of −0.43 ± 0.14 s (the
alert would speed jobs up) and distorts storage (1.03 s) and the common shift (0.73 s). Both models fit
well; only one is consistent with the mechanisms. A high R² is also expected here by construction: the
indicators were chosen *after* looking at which jobs were slow, and per-job means average away step
noise.

**Common wrong answers.** "R² is high so the model is correct"; "R² is high so there are no other
causes"; confusing R² with statistical significance of individual coefficients.
