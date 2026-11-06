# K4 — Why rack power budgets use maximum node power

**Source:** manuscript Section 23.4 (Table 23.5 invariant 11, "Use maximum power for budgets");
docs/REFERENCE_CLUSTER.md (node power ≈ 10.2 kW max, ≈ 8–9 kW sustained `[ILLUSTRATIVE]`); key K4.

**Reason.** A rack budget is a hard electrical limit: the branch-circuit breaker and PDU rating after
derating. Exceeding it, even for seconds, trips the circuit and takes down every node in the rack,
regardless of how low the average draw is. Budgets must therefore survive the worst case. On ORION,
4 nodes × 10.2 kW = 40.8 kW ≤ 45 kW planned `[MODELED]`. Sizing with sustained power (≈ 8.5 kW) would allow
floor(45 / 8.5) = 5 nodes = 51 kW at maximum, which is 6 kW over budget: the Kestrel bundle's
POWER-001 defect.

**Events that drive a rack toward its maximum** (any two):
1. **Synchronized step-start power spikes.** All 32 GPUs in a rack start the compute phase of a
   training step at the same instant, so their power rises together rather than averaging out.
2. **Burn-in and acceptance stress tests.** Node acceptance (Chapter 16) deliberately runs GPUs at
   full power for hours, typically on a whole rack at once.
3. **Firmware or driver changes to power capping.** An update that changes or removes the GPU power
   cap raises the maximum without any change to the job.
4. **Loss of one PDU feed.** With A/B feeds, the surviving feed carries the whole rack's load and
   must be rated for it.

**Transient margin.** Chapter 21 plans peak rack load to ≤ 90 % of the rack limit so synchronized
step-change transients have headroom. Planned budget = 50 kW × 0.9 = **45 kW**; nodes per rack =
floor(45 / 10.2) = floor(4.41) = **4** (40.8 kW, 4.2 kW spare) `[MODELED]`. This is the budget the
worked example uses (A-09, a declared variation from the canonical 2 × 32.78 kW circuits per side).

**Common wrong answers.** "Because average power is hard to measure" (the issue is the breaker, not
measurement); citing "the job runs hotter at night" without a mechanism; using GPU TDP alone and
forgetting the ≈ 4.6 kW base (CPUs, memory, NICs, fans, PSU loss) from the node power model.
