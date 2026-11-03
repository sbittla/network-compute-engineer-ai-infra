# 6.13 — Is the improvement real? (model answer, 10 points)

Relies on manuscript Section 6.7 (statistics and decision rule) and Section 6.9 (worked example). Computed with
the lab's reference `permutation_test` and `bootstrap_ratio_ci` (seed 11, 4,000 replicates); `solve.py`
reproduces and asserts every value `[MODELED]`.

**Medians (2 points).**

- Baseline sorted: 12.37, 12.39, 12.41, 12.44, 12.47, 12.52 → (12.41 + 12.44) / 2 = **12.425 ms**.
- Candidate, all six: 12.05, 12.10, 12.12, 12.22, 12.31, 12.95 → (12.12 + 12.22) / 2 = **12.17 ms**.
- Candidate without run 5: 12.05, 12.10, 12.12, 12.22, 12.31 → **12.12 ms**.

**Relative changes (2 points).** 12.17 / 12.425 − 1 = **−2.05 %**; 12.12 / 12.425 − 1 = **−2.45 %**.

**Tests (3 points).**

| | Bootstrap 95 % band | Exact permutation *p* | Splits enumerated |
|---|---|---|---|
| All runs (6 + 6) | [−2.97 %, +1.65 %] | **0.36** | C(12, 6) = 924 |
| Without run 5 (6 + 5) | [−3.16 %, −0.85 %] | 1/462 = **0.002** | C(11, 5) = 462 |

**Decisions and justification (3 points).** With all runs: *p* = 0.36 → **not significant**. Without run 5:
*p* = 0.002 and |−2.45 %| ≥ max(0.9 %, 2 %) → **improvement**.

The exclusion rests on the **clock**, not on the event: `sw_power_cap` alone is routine (Section 6.5), but
run 5's median clock is 1,610 / 1,826 = 88 % of the peer median, below the 95 % rule. The other eleven runs
of both arms sit at 1,822–1,830 MHz, so the change does not move the clock and a session-wide peer clock is
valid. The second decision stands **only if** that rule was part of the pre-registered protocol and is applied
to *both* arms (the baseline's runs pass it). Excluding a run only because it hurts the candidate is
p-hacking. With the effect this close to the 2 %
threshold, the defensible recommendation is to rerun that run and collect ≥ 10 runs per arm before shipping.

**Common wrong answers.** Taking the mean (12.46 ms for the candidate, pulled up by run 5) instead of the median; permutation tests on iterations;
declaring an improvement from −2.05 % alone; excluding run 5 without stating the rule, or because `sw_power_cap` was logged.
