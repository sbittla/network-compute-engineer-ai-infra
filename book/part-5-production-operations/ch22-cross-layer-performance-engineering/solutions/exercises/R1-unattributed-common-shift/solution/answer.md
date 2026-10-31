# R1 — Explaining the unattributed common shift (solution)

**What is being explained.** The period indicator carries +0.34 ± 0.09 s per step, 8.3 % of the 4.04 s
delta (± 1.7 pp HC3 for this event, 95 % ≈ 5–12 %; job-level bootstrap 4–14 %) `[SIMULATED]`. It is
real (≈ 3.7 SE from zero) but not attributable to a named change (Section 22.4.2).

| Explanation | Evidence that supports it | Separating test |
|---|---|---|
| (i) The container rebuild CHG-7802 changed something despite "framework versions unchanged" (a library, a compiler flag, a security patch with a runtime cost) | It is the only change that touched *all* after-period jobs; its recorded validation was a smoke test, which does not measure step time | A/B of old vs new container digest on reserved nodes with everything else fixed, 5 interleaved runs per arm (MDE ≈ 0.19 s, so a 0.34 s shift is detectable); diff the image package lists offline first |
| (ii) An unmodeled interaction or non-linear effect (for example straggler effects that grow when several factors coincide) | The additive-plus-one-interaction model may leave structure in the residuals by job type | Fit extra interaction terms (O1-c) and inspect residuals by cell; if the shift moves into a term, it was model misspecification |
| (iii) A time-varying environmental factor coincident with the window (neighbour load on the fabric, facility temperature) | Nothing in the bundle measures it: missing evidence | Check neighbour job load and facility telemetry for the after period; compare with a pinned canary that ran across the window |

**Order to run them.** The package-list diff and the residual check are offline and cost minutes; run
them first. The container A/B costs reserved node-hours and confirms (i) directly.

**Common wrong answers.** Attributing the shift to the largest named change ("it is probably placement");
treating 8.3 % as noise despite a 3.7 SE effect; naming three variants of one explanation.
