# R1 — The assumption with the highest decision value (model answer)

**Source:** manuscript Section 23.2 ("Rank by decision value, not by uncertainty"), Section 23.9
(Table 23.10), Section 23.10; key R1.

**Model answer (≈ 120 words).** The highest-value assumption is MFU, A-04 = 0.40 `[ILLUSTRATIVE]`. It
sets W-TRAIN's 17.4 s step time and therefore the run length: moving MFU from 0.40 to 0.35 adds about
14 days to a 96-day run (Section 23.2), which decides whether the 120-day objective holds and whether a
second cluster purchase is needed. The cheapest test is a 64-GPU slice of W-TRAIN (TP = 8, PP = 4, DP = 2)
for 100 steps after warm-up, 5 repetitions, with a manifest, at L3 (or a single-node L2 run with PP and
DP stubbed, as a weaker bound). Acceptance: median MFU ≥ 0.37 keeps the plan; below that, re-plan the
schedule. Table 23.10 already ranks it first (score 2.25).

**Accepted alternative.** Checkpoint δ, A-08 = 60 s: a single-node save timing at L2 bounds it, and an
async δ ≈ 5 s would cut failure waste from 3.16 % to ≈ 1.28 %.

**Deduct for** naming an assumption without the decision it changes, or a "test" with no tier and no
acceptance criterion.
