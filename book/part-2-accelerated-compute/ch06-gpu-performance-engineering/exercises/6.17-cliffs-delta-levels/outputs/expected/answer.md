# 6.17 — Cliff's δ on iterations vs run medians (model answer, 3 points)

Relies on manuscript Section 6.7 (effect sizes) and Section 6.9 (worked example). Values `[SIMULATED]` data.

Cliff's δ = P(candidate < baseline) − P(candidate > baseline) over all cross-pairs: it measures how often one
sample's values exceed the other's, and its value depends on the **level** at which it is computed. For
candidate C on single iterations, δ = −0.28 ("small"): individual iterations of the two arms overlap heavily,
because within-run noise (≈ 1–2 %) dwarfs a 0.45 % shift. On run medians, within-run noise is averaged away and
the run distributions are tight: of the 6 × 5 = 30 run pairs, 25 favour C and 5 favour A, so
δ = (25 − 5) / 30 = −0.67 ("large"), yet the change is only 0.45 %.

Lesson: effect sizes describe separation, not practical value. State the level, and always pair δ with the
relative change and the practical threshold (here below the 1 % bar: "below_threshold").

(≈ 145 words.)
