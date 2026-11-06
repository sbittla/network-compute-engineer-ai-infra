# 10.H1 — Link-health analyzer and commissioning report (★★★, L1)

**Type:** Hands-on lab · **Kind:** lab · **Points:** 100

## Prompt

<!-- prompt:start -->
**10.H1 — Link-health analyzer and commissioning report.** Complete [lab/README.md](../../lab/README.md)
tasks 1–8 for `orion-be-leaf-r3`.
*Evidence required:* `python check.py` output showing that all checks pass (the data-regeneration check may report SKIP); the generated
`commissioning-report.md`; `diagnosis.md` explaining every non-healthy port (evidence, layer, root
cause hypothesis, first safe action, missing hardware evidence) and every decoy you identified.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/check.txt`: the output of `python check.py`: every check PASS (`dataset_reproducible` may report SKIP in the student release)
- `outputs/commissioning-report.md`: written by `python check.py --report`
- `outputs/diagnosis.md`: every non-healthy port and every decoy explained
- `outputs/linkhealth.py`: a copy of your completed `lab/starter/linkhealth.py`

Label the dataset `[SIMULATED]` and your derived numbers `[MODELED]`.

Run from the chapter folder:

```bash
cd lab
python check.py --report ../exercises/10.H1-link-health-analyzer/outputs/commissioning-report.md
```
