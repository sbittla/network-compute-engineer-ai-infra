# R1 — Capacity-model assumptions to measure (★, L1)

Type: reflection · Kind: written

## Prompt

<!-- prompt:start -->
**R1. ★ L1.** Which three assumptions in the lab's capacity model would you most want to measure
on real hardware, and why those three?
*Evidence required:* three named parameters, the output each one drives, and the L2/L3
measurement that would replace it.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.

To see two of these measurements on real hardware, run `python scripts/hw_labs.py run ch15 --device gpu`
(CPU fallback with `--device cpu`) and read `lab/l2/results/*/report.md`: the implied `hbm_efficiency`,
step overhead and `prefill_mfu` for that stack.
