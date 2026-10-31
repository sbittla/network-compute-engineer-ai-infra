# 6.20 — Keep run A3: recompute C vs A (model answer, 3 points)

Relies on manuscript Section 6.7 (decision rule, pre-registration) and Section 6.9. Recomputed with the lab's
reference `compare()` on `lab/data` `[SIMULATED]`; `solve.py` asserts the values.

| Protocol | Baseline runs | Change | 95 % band | Permutation *p* | Decision |
|---|---|---|---|---|---|
| With version rule (A3 excluded) | 5 | −0.50 % | [−0.82 %, +0.18 %] | 0.026 | below_threshold |
| Without it (A3 kept) | 6 | **−0.44 %** | **[−0.77 %, +1.19 %]** | **0.99** | **not_significant** |

A3 ran on PyTorch 2.3.1, whose kernel selection is ≈ 2.7 % faster; kept among A's runs, it drags the baseline
spread wide and the "small real effect" disappears.

Which answer is right depends on a rule decided *before* the data were seen and applied to every arm.
Excluding A3 because it is a different experiment (wrong container) is legitimate; excluding it because it
makes C look worse would not be. Pre-registration plus symmetric application is what makes exclusions
defensible; otherwise the analyst's choices become a hidden degree of freedom (p-hacking).

(≈ 140 words.)
