# 6.20 — Keep run A3: recompute C vs A (model answer, 3 points)

Relies on manuscript Section 6.7 (decision rule, pre-registration) and Section 6.9. Recomputed with the lab's
reference `compare()` on `lab/data` `[SIMULATED]`; `solve.py` asserts the values.

| Protocol | Baseline runs | Change | 95 % band | Permutation *p* | Decision |
|---|---|---|---|---|---|
| With version rule (A3 excluded) | 5 | −0.45 % | [−0.72 %, −0.12 %] | 0.026 | below_threshold |
| Without it (A3 kept) | 6 | **−0.01 %** | **[−0.65 %, +0.93 %]** | **0.99** | **not_significant** |

Change, band and *p* all use the lab's primary statistic (difference in arm means of run medians, % of the
baseline mean).

A3 ran on PyTorch 2.3.1, whose kernel selection is ≈ 2.7 % faster; kept among A's runs, it pulls the
baseline mean down and the spread wide, and the "small real effect" disappears.

Which answer is right depends on a rule decided *before* the data were seen and applied to every arm.
Excluding A3 because it is a different experiment (wrong container) is legitimate; excluding it because it
makes C look worse would not be. Pre-registration plus symmetric application is what makes exclusions
defensible; otherwise the analyst's choices become a hidden degree of freedom (p-hacking).

(≈ 140 words.)
