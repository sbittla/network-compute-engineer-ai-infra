# 20.1.6 — Proceed, hold and abort: worked answer

**Relies on:** manuscript Section 20.7.1 (vocabulary, Figure 20.4), Section 20.7.4 (Table 20.9 abort
conditions) and the lab decision log of Section 20.11, Table 20.13 `[SIMULATED]`.

## Model answer

A rollout controller evaluates each wave after its bake and returns one of three decisions:

- **Proceed**: every changed node has a full set of bake samples (12 at 5-minute intervals over 60 min in
  the lab) and no pre-declared abort condition is breached. *Example:* lab wave 0 (`orion-n01`,
  `orion-n05`): busbw medians within 5 % of their own baselines, no Xids, no flaps → start wave 1.
- **Hold**: the evidence is insufficient to decide. *Example:* the telemetry pipeline dropped samples and a
  changed node has fewer than 12 post-change samples, or the bake time has not elapsed (the lab's
  `p2.bake_insufficient_hold` case). The controller neither proceeds nor rolls back; a human investigates
  the evidence gap first.
- **Abort**: any pre-declared condition is breached. *Example:* lab wave 2, `orion-n25`: median per-rail busbw
  39.41 GB/s against a 43.67 GB/s baseline median (−9.8 %, beyond AC1's 5 %), and CNP median 986/s against
  200/s (more than 3 × baseline and above the 500/s floor, AC2). The rollout stops and rollback runs at the
  declared scope.

**Hold is not abort.** Hold means "we cannot tell yet"; abort means "we can tell, and it is bad". Treating
missing data as a pass is the most dangerous controller bug; treating it as an abort teaches operators to
override the controller.

## Marking notes (4 points)

1 point per decision with a concrete condition; 1 point for stating that hold triggers no rollback and no
progress.

**Common wrong answers.** Hold described as "wait a bit and proceed automatically". Abort conditions invented
after the rollout starts rather than declared before it.
