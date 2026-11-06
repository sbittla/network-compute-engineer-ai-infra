# 12.13 — nccl-tests analysis toolkit (lab) (★★, L1)

**Type:** Hands-on lab · **Kind:** lab · **Points:** 100

## Prompt

<!-- prompt:start -->
**12.13 ★★ L1 — nccl-tests analysis toolkit (lab).** Complete [lab/README.md](../../lab/README.md) tasks 1–6
so that `python lab/check.py` passes. Optional: run `lab/optional/gloo_allreduce.py` on your laptop if
PyTorch is installed and parse your own output.
*Evidence required:* checker output (11/11 PASS), summary table, anomaly labels with explanations,
and (optional) your gloo log labelled `[MEASURED]` with the environment.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 12 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/check.txt`: checker output showing `11/11 checks passed`
- `outputs/summary.md`: the six-row summary table and the anomaly labels with explanations
- `outputs/gloo.log`: optional: your own gloo run, labelled `[MEASURED]` with the environment

Label lab data `[SIMULATED]`, fits `[MODELED]`, and your own optional run `[MEASURED]`.

Run from the chapter folder:

```bash
python lab/check.py
```
