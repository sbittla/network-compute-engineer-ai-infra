# Marking scheme: 6.13 Is the improvement real?

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** arm means of the run medians, relative changes, p-values, bootstrap bands, decisions, justification.

| Criterion | Points |
|---|---|
| Arm means of run medians: baseline 12.4333 ms, candidate 12.2917 ms (all runs) and 12.16 ms (without run 5) | 2 |
| Relative changes (same statistic as the band and the test): −1.14 % and −2.20 % | 2 |
| Tests: bootstrap bands [−2.69 %, +1.14 %] and [−2.90 %, −1.42 %]; exact permutation p = 0.36 and 0.002 | 3 |
| Decisions (not significant vs improvement) and justification: exclusion rests on the clock (1,610 / 1,826 = 88 % < 95 %), not on sw_power_cap, and stands only if pre-registered and applied to both arms | 3 |
