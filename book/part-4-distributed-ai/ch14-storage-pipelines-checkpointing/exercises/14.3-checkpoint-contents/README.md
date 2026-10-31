# 14.3 — What is in a checkpoint (★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**14.3 What is in a checkpoint** ★ · L1
Explain why W-TRAIN's checkpoint is 14 B/param while its training state is 16 B/param. List three
non-tensor items that a checkpoint must contain for a resume to be equivalent, and what goes wrong
without each. *Evidence required:* the byte breakdown and three item → consequence pairs.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
