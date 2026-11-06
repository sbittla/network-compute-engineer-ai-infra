# 6.13 — Is the improvement real? (model answer, 10 points)

Relies on manuscript Section 6.7 (statistics and decision rule) and Section 6.9 (worked example). Computed with
the lab's reference `permutation_test` and `bootstrap_ratio_ci` (seed 11, 4,000 replicates); `solve.py`
reproduces and asserts every value `[MODELED]`. One statistic throughout, the lab's primary statistic: the
difference in arm means of the run medians, as a % of the baseline mean. The change, the band and the test
all use it.

**Arm means of the run medians (2 points).**

- Baseline: 74.60 / 6 = **12.4333 ms**.
- Candidate, all six: 73.75 / 6 = **12.2917 ms** (pulled up by run 5's 12.95 ms).
- Candidate without run 5: 60.80 / 5 = **12.16 ms**.

**Relative changes (2 points).** (12.2917 − 12.4333) / 12.4333 = **−1.14 %**;
(12.16 − 12.4333) / 12.4333 = **−2.20 %**.

**Tests (3 points).**

| | Bootstrap 95 % band | Exact permutation *p* | Splits enumerated |
|---|---|---|---|
| All runs (6 + 6) | [−2.69 %, +1.14 %] | **0.36** | C(12, 6) = 924 |
| Without run 5 (6 + 5) | [−2.90 %, −1.42 %] | 1/462 = **0.002** | C(11, 5) = 462 |

**Decisions and justification (3 points).** With all runs: *p* = 0.36 → **not significant**. Without run 5:
*p* = 0.002 and |−2.20 %| ≥ max(0.9 %, 2 %) → **improvement**.

*Sensitivity analysis (median of run medians, not the decision):* baseline 12.425 ms; candidate 12.17 ms
(all runs) → −2.05 %, *p* = 0.041; 12.12 ms (without run 5) → −2.45 %, *p* = 0.013. With all six runs the
median statistic would call the candidate an improvement while the primary statistic says not significant.
The decision depends on the statistic, which is why the statistic is pre-registered and the other one is
only reported.

The exclusion rests on the **clock**, not on the event: `sw_power_cap` alone is routine (Section 6.5), but
run 5's median clock is 1,610 / 1,826 = 88 % of the peer median, below the 95 % rule. The other eleven runs
of both arms sit at 1,822–1,830 MHz, so the change does not move the clock and a session-wide peer clock is
valid. The second decision stands **only if** that rule was part of the pre-registered protocol and is applied
to *both* arms (the baseline's runs pass it). Excluding a run only because it hurts the candidate is
p-hacking. With the effect this close to the 2 %
threshold, the defensible recommendation is to rerun that run and collect ≥ 10 runs per arm before shipping.

**Common wrong answers.** Reporting a change of medians beside a band or test of means (or choosing whichever
statistic gives the better answer); permutation tests on iterations; declaring an improvement from the median
statistic's −2.05 % with all runs; excluding run 5 without stating the rule, or because `sw_power_cap` was logged.
