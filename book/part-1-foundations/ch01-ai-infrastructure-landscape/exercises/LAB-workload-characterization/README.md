# Exercise LAB — Workload-characterization lab

**Difficulty:** ★★ · **Tier:** L1 · **Type:** hands-on-lab · **Kind:** lab · **Points:** 100

## Prompt

<!-- prompt:start -->
Complete the workload-characterization lab in [lab/README.md](../../lab/README.md): implement
`starter/workload_model.py` until `python check.py` passes, then write the one-page comparison for W01
vs W02 and a short data-quality note listing every row you rejected or flagged and why.

**Evidence required:** `check.py` output showing 9/9 PASS; the generated comparison Markdown; the
data-quality note (one line per rejected/flagged row with the root-cause hypothesis for the flaw).
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 1 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/check.txt`: the `check.py` output showing 9/9 PASS
- `outputs/comparison.md`: the generated W01 vs W02 one-page comparison
- `outputs/data_quality.md`: one line per rejected or flagged row with the root-cause hypothesis and an owner

Command to run (from this folder):

```bash
cd ../../lab && python check.py | tee ../exercises/LAB-workload-characterization/outputs/check.txt
python starter/workload_model.py --compare W01 W02 > ../exercises/LAB-workload-characterization/outputs/comparison.md
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
