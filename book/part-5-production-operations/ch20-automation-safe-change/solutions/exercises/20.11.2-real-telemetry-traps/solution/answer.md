# 20.11.2 — What real telemetry would do: model answer

**Relies on:** manuscript Section 20.7.4 ("make no data a hold"), the Realism boundaries section, and lab Part 2
(`rollout.json`, `[SIMULATED]`).

## Model answer (≤ 150 words)

1. **Gaps and late samples.** Collectors drop or delay points. A controller that counts only received samples
   may proceed on 4 of 12 (false proceed) or, if late samples land in the next window, abort a wave for another
   wave's data. Handling: require the full sample count, otherwise hold.
2. **Counter resets and wraps.** A NIC reset or a 32-bit wrap makes a derived rate negative or huge: a CNP rate
   of 10⁹/s trips AC2 (false abort), a negative rate hides a real rise (false proceed). Handling: reset-aware rate
   computation, and a sanity range.
3. **Correlated fleet-wide shifts.** A new tenant job, a changed message size or another change in flight shifts
   every node, so a baseline from a different load regime makes the change look guilty or innocent. Handling:
   compare with unchanged control nodes in the same window.

## Marking (5 points)

Three behaviours 3 · how each fools the controller and the handling 2.
