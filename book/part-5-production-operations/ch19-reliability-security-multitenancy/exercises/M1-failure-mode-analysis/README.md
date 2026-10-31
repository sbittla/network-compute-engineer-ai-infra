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

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/risk_register.csv (or .md)`
- `outputs/top5_actions.md`
