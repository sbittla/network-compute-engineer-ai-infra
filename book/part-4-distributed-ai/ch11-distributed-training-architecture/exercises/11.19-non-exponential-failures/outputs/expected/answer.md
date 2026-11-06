# 11.19 — A failure pattern that breaks Young/Daly's assumption

Young/Daly assumes exponentially distributed failures: a constant hazard rate, so the probability of
failing in the next hour is the same whether the job started a minute or a week ago, and failures are
independent.

**Real pattern: infant mortality after maintenance.** After a firmware rollout, a rack's re-cabling, or
node replacements, the hazard rate is high for the first hours or days (marginal parts, mis-seated
cables, bad firmware), then falls — a decreasing hazard (Weibull shape < 1), not a constant one. Failures
also cluster: several nodes from the same maintenance batch fail in the same window.

Other valid patterns: **correlated failures** (a rack PDU or a spine switch takes out many nodes at once,
so one "failure" costs more restart and the events are not independent); **wear-out** (rising hazard
late in component life).

**How it changes the policy.**

- Use a **per-period MTBF**: after maintenance, use the measured post-maintenance MTBF (e.g. 4× lower)
  and shorten τ by √4 = 2× (τ ∝ √MTBF); return to the steady-state interval once the burn-in window has
  passed without failures.
- Around known-risky events (rollouts, cooling work, a spine upgrade) checkpoint immediately before and
  shorten τ during the window.
- Burn in replaced nodes *before* they join the training partition, so the infant-mortality period is
  spent outside the job.
- For correlated failures, size R for the multi-node case (more nodes to replace) and keep spare
  capacity in a different failure domain.

Re-estimate MTBF monthly from the job's own failure log (Section 11.12).
