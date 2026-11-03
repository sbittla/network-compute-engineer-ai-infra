# K7 — Survivorship bias in regression analysis (solution)

**Definition in this context.** Survivorship bias means analyzing only the jobs that completed (or only
"healthy" runs on the dashboard) while the regression's population is every job launched. The excluded
jobs are not a random sample: the jobs most affected by a regression are the ones most likely to fail,
so dropping them removes the strongest evidence and shrinks the measured effect (Section 22.8,
Table 22.9).

**Why placement regressions are hit hardest.** A job whose TP group is split across nodes moves its TP
all-reduces from NVLink onto the backend NICs. That makes it the slowest job *and* the one that drives
the most fabric traffic (lab: backend tx per node 6 → 96 GB/s `[SIMULATED]`), with many more
latency-sensitive collectives per step. It is therefore the job most likely to hit an NCCL collective
timeout and fail. The cause of the slowdown is also the cause of the failure, so filtering on
`status == COMPLETED` selects *against* the cause.

**Lab numbers (`solve.py`, `[SIMULATED]`).** Job 41114 is TP-split, failed with an NCCL timeout after 60
usable steps:

| Statistic | All 48 jobs | Excluding failed 41114 |
|---|---|---|
| Headline mean change | +23.2 % | +21.9 % |
| TP-split share of the delta | 64.7 % | 61.4 % |
| Common-shift share | 8.3 % | 8.9 % |

The cause ranking survives, but the placement change looks smaller than it is, exactly the factor the
failed job belonged to.

**Correct practice.** Population = every job launched; report failures separately *and* include their
usable steps; when cost matters, also report the step-weighted (GPU-hour) change, which down-weights a
short failed job transparently (+22.3 %) instead of dropping it.

**Common wrong answers.** Treating survivorship bias as "small sample size"; arguing failed jobs should be
dropped because they are "outliers".
