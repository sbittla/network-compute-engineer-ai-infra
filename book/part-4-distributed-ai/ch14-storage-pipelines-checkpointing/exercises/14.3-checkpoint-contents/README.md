# 14.3 — What is in a checkpoint (★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**14.3 What is in a checkpoint** ★ · L1
Explain why W-TRAIN's checkpoint is 14 B/param while its training state is 16 B/param. List three
non-tensor items that a checkpoint must contain for a resume to be equivalent, and what goes wrong
without each. *Evidence required:* the byte breakdown and three item → consequence pairs.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/14.3-checkpoint-contents/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
