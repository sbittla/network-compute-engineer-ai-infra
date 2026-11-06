# 13.12 — Cross-layer straggler diagnosis (lab) (★★, L1)

Type: hands-on-lab · Kind: lab

## Prompt

<!-- prompt:start -->
**13.12 ★★ L1 — Cross-layer straggler diagnosis (lab).** Complete [lab/README.md](../../lab/README.md) so
that `python lab/check.py` passes and write the diagnosis report.
*Evidence required:* checker output (11/11 PASS), findings table (cause, ranks, onset, evidence,
owner, fix, validation), amplification numbers, and the annotated diagram from 13.9.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/check_output.txt`
- `outputs/diagnosis_report.md`

Run:

```bash
python lab/check.py
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
