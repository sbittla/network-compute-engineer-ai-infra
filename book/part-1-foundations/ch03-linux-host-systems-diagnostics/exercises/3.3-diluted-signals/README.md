# Exercise 3.3 — Diluted signals

**Difficulty:** ★ · **Tier:** L1 · **Type:** knowledge-check · **Kind:** computed · **Points:** 4

## Prompt

<!-- prompt:start -->
A 224-CPU host shows `%iowait` = 4.5 % and a load average of 12 while 92 % idle. (a) What is the largest
number of blocked tasks consistent with that `%iowait`? (b) Which two undiluted metrics would you
check next?
*Evidence required:* the arithmetic, and the two metrics with the command that shows each.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 3 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your answer with the evidence the prompt requires

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
