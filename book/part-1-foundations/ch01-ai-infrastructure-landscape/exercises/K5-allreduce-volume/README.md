# Exercise K5 — Bandwidth-optimal all-reduce volume

**Difficulty:** ★ · **Tier:** L1 · **Type:** knowledge-check · **Kind:** computed · **Points:** 4

## Prompt

<!-- prompt:start -->
**K5.** What is the per-participant send volume of a bandwidth-optimal all-reduce of *S* bytes among
*p* participants? Evaluate the factor for *p* = 4 and *p* = 8.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/K5-allreduce-volume/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your worked answer: formula, substitution, result with units and evidence label

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
