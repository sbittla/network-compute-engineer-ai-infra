# M3 · Lifecycle state machine (★★ · L1)

Type: outline-mandated · Kind: lab · Points: 15

<!-- prompt:start -->
**M3 ★★ (L1) [Outline] — Lifecycle state machine.** Write the node lifecycle state machine with
states discovered, imaged, validated, schedulable, draining, drained, repair, and retired: every
allowed transition with its event, guard, side effects, and audit fields; and the transitions you
deliberately forbid, with the reason. Implement it (lab Task 3) and show the rejected events from the
replay.
*Evidence required:* a diagram; a transition table; a forbidden-transition table; `check.py` T3.*
checks passing.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass.

## What to submit

Put these files in `outputs/`:

- `check_output.txt` — the checker report, captured from the chapter folder with
  `cd lab && python check.py > ../exercises/M3-lifecycle-state-machine/outputs/check_output.txt`
- `state_machine.md` — diagram, transition table, forbidden-transition table, and the rejected
  events from the replay (lab Task 3)
