# O3 — Before/after report for the change owners (★★★, L1)

Outline-mandated · difficulty ★★★ · tier L1 · kind `lab` · [exercise index](../README.md)

<!-- prompt:start -->
**O3 ★★★ (L1; L3 optional) — Write a before/after report that separates measured facts, inferred causes,
and remaining uncertainty.**
a. Complete lab task 9, then edit the generated report into a one-page document for the four change
   owners, following Section 22.9.
b. Include the data-hygiene rules applied and their effects, and the verdict on the `orion-n13` alert with
   its evidence.
c. Add a "Recommended changes and validation" section: for each fix, the predicted effect (range), the
   canary scope, the MDE for your proposed n, and an abort condition. L3 learners execute the
   placement A/B from the lab README and add the results labelled `[MEASURED]` with a manifest.
*Evidence required:* the report; every number labelled; no causal language in "Measured facts".
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 22 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Numbers in prompts are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/report.md`

Run:

```bash
python ../../lab/starter/regression_lab.py --report outputs/report.md   # then edit to one page
```

On a single GPU host, `python scripts/hw_labs.py run ch22 --device gpu` produces a before/after report on injected
regressions with known ground truth (CPU fallback with `--device cpu`). Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.