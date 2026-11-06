# 11.13 — Step-time and memory model (lab) (★★, L1)

**Type:** Hands-on lab · **Kind:** lab · **Points:** 100

## Prompt

<!-- prompt:start -->
**11.13 ★★ L1 — Step-time and memory model (lab).** Complete [lab/README.md](../../lab/README.md) tasks
1–6 so that `python lab/check.py` passes, and write the lab report.
*Evidence required:* checker output (10/10 PASS), candidate table, recommendation with justification,
checkpoint table, and a paragraph on the planted traps.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/check.txt`: checker output showing `10/10 checks passed`
- `outputs/candidates.md`: the candidate table (memory, bubble, step, MFU, reasons)
- `outputs/report.md`: recommendation with justification, checkpoint table, paragraph on the planted traps

Label every number `[MODELED]`; the model's inputs are `[ILLUSTRATIVE]` (Table 11.4).

Run from the chapter folder:

```bash
python lab/check.py
```
