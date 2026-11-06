# 14.11 — Progressive Lab 6 — Storage and checkpoint (★★, L1 (L2/L3 extensions))

Type: hands-on-lab · Kind: lab

## Prompt

<!-- prompt:start -->
**14.11 Progressive Lab 6 — Storage and checkpoint** ★★ · L1 (L2/L3 extensions) **(outline)**
Complete [lab/README.md](../../lab/README.md) Parts A–C until `python check.py` reports 15/15, and write
the two-page memo described in lab Section 7. *Evidence required:* checker output and the memo.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/check_output.txt`
- `outputs/memo.md (two pages, lab Section 7)`

Run the checker from the chapter's `lab/` folder (the `python check.py` of the prompt), and save its output:

```bash
cd ../../lab                       # from this exercise folder
python check.py                    # 15/15 PASS when done
python check.py > ../exercises/14.11-storage-checkpoint-lab/outputs/check_output.txt
```

`python lab/check.py` from the chapter folder runs the same checker; it locates its files relative to itself.

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
