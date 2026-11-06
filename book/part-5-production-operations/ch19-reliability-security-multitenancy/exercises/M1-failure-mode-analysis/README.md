# M1 — Failure-mode analysis (risk register) (★★, L1)

Type: Outline-mandated · Kind: `lab` · Points: 15

## Prompt

<!-- prompt:start -->
**M1 ★★ L1 — Failure-mode analysis.** Perform an FMEA for **GPU node, rack, leaf switch, storage,
scheduler, and control-plane** failures on ORION-XL: failure modes, effects on training and inference,
S/O/D with justification, RPN and action priority, detection controls, mitigations, owners.
*(Deliverable: risk register.)* The lab's `fmea_score()` may be used to rank it.
*Evidence required:* ≥ 12 rows covering all six domains; corrected scores; top-5 actions with owners.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 19 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/risk_register.csv` (or .md)
- `outputs/top5_actions.md`
