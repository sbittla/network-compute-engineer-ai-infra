# K5 — TP inside the node (★★, L1)

Knowledge check · difficulty ★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**K5 ★★ L1 — TP inside the node.** State the calculation from Section 24.6 that shows TP = 8 must stay
inside the NVLink domain for W-TRAIN. Give the per-step TP volume per GPU and the time it would take
over NVLink and over a NIC under the chapter's assumptions.
*Evidence required:* formula, substituted values, both times with units and labels.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 24 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python outputs/work.py   # optional: your own script, if you script the arithmetic
```
