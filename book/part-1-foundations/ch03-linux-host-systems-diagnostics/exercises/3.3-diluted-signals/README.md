# Exercise 3.3 — Diluted signals

**Difficulty:** ★ · **Tier:** L1 · **Type:** knowledge-check · **Kind:** computed · **Points:** 4

## Prompt

<!-- prompt:start -->
A 224-CPU host shows `%iowait` = 4.5 % and a load average of 12 while 92 % idle. (a) What is the largest
number of blocked tasks consistent with that `%iowait`? (b) Which two undiluted metrics would you
check next?
*Evidence required:* the arithmetic, and the two metrics with the command that shows each.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your answer with the evidence the prompt requires

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
