# WP1 — Readiness for a second role: worked solution

**Method** (manuscript Section 24.2, "A worked readiness calculation"; matrix `sre_ops` in
`lab/data/competency_matrices.yaml`). Readiness = 100 × Σ w·min(d, t)/t ÷ Σ w, where d is the demonstrated
level and t the target at the chosen seniority. Status rules (`evidence_rules`): **ready** if score ≥ 85
*and* every gap t − d ≤ 1; **near** if score ≥ 70; otherwise **not_ready**. All values `[MODELED]` from
self-reported, rule-adjusted evidence.

**(a) Table at mid level**

| Competency | w | d | t (mid) | min(d,t)/t | w × fraction |
|---|---|---|---|---|---|
| observability | 3 | 1 | 3 | 0.333 | 1.000 |
| reliability_security | 3 | 2 | 2 | 1.000 | 3.000 |
| automation | 2 | 3 | 2 | 1.000 | 2.000 |
| scheduling | 2 | 1 | 2 | 0.500 | 1.000 |
| storage_ckpt | 1 | 1 | 2 | 0.500 | 0.500 |
| linux_host | 2 | 2 | 2 | 1.000 | 2.000 |
| communication | 2 | 3 | 2 | 1.000 | 2.000 |
| **Σ** | **15** | | | | **11.500** |

Readiness = 100 × 11.500 / 15 = **76.7 %**.

**(b) Status: near.** 76.7 ≥ 70 but < 85, and independently the observability gap is 3 − 1 = 2, which
blocks "ready" at any score (the gap-blocks-ready rule).

**(c) Gap plan, priority = w × gap:** observability 3 × 2 = **6** (Chapter 18; Capstones B or F),
scheduling 2 × 1 = **2** (Chapter 17; Capstones E or G), storage_ckpt 1 × 1 = **1** (Chapter 14;
Capstones C or G). Target 3 needs capstone, hardware-lab or case-study evidence; target 2 needs an L1 lab.

**(d) Capstone F raises observability to 3:** its term becomes 3 × 3/3 = 3.000 (+2.000), so Σ = 13.500 and
readiness = 100 × 13.5 / 15 = **90.0 %**. The largest remaining gap is 1 (scheduling, storage), so the
status is **ready**.

**Common wrong answers.** Using the senior targets; letting automation's d = 3 count as 1.5 (the fraction
caps at 1.0); calling 76.7 % "ready" or ignoring the gap rule; ordering the gap plan by gap size instead of
weight × gap. `solve.py` reads the matrix from the lab data and asserts 76.7 %, near, the ordered plan and
90.0 % ready.
