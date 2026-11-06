# 6.6 — Why the run, not the iteration, is the unit of replication (model answer, 3 points)

Relies on manuscript Section 6.7 (statistics) and Section 6.9 (worked example).

**Correlation argument (1 point).** All iterations of one process share the same memory allocations and
addresses, kernel and algorithm selection (cuBLAS heuristics, autotuning), GPU and CPU placement, clock and
thermal state, and the state of other tenants. Whatever made this run fast or slow affects all its iterations
together, so the iterations are **positively correlated**, not independent samples. A new run (fresh process)
re-draws all those factors; the variation between runs is typically larger than the variation within one.

**What goes wrong with a CI from 300 iterations of one run (1 point).** It estimates only the within-run noise
and treats 300 correlated samples as 300 independent ones. It says nothing about run-to-run variation, which
is often the larger component. The standard error shrinks with √300, so the interval is **far too narrow**.

**Consequence (1 point).** False positives: two arms that differ only because each was measured in one run
(different allocation, kernel choice or clock) appear "significantly" different, and a real effect cannot be
distinguished from run luck. Lab 6 shows the effect size changing level too: Cliff's δ for candidate C is
−0.28 on iterations but −0.67 on run medians.

**Correct practice.** Run several independent processes per arm (≥ 5), summarize each by its median, and do
inference on run medians (exact permutation test, bootstrap over runs), with an A/A floor measured the same
way.
