# L1 — Lab 15: capacity model, serving-trace analyzer, disaggregation model (★★, L1)

Type: hands-on-lab · Kind: lab

## Prompt

<!-- prompt:start -->
**L1. ★★ L1 — Lab 15: capacity model, serving-trace analyzer, disaggregation model.** Complete
[lab/README.md](../../lab/README.md) Tasks 1–10.
*Evidence required:* `python check.py` output with 19/19 PASS, and the two-page report described
in lab Section 8.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 15 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/check_output.txt`
- `outputs/report.md (two pages, lab Section 8)`

Run the checker from the chapter's `lab/` folder (the `python check.py` of the prompt), and save its output:

```bash
cd ../../lab                       # from this exercise folder
python check.py                    # 19/19 PASS when done
python check.py > ../exercises/L1-serving-lab/outputs/check_output.txt
```

`python lab/check.py` from the chapter folder runs the same checker; it locates its files relative to itself.

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
