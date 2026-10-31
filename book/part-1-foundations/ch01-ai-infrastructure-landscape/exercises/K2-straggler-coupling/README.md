# Exercise K2 — Why one slow GPU slows the whole job

**Difficulty:** ★ · **Tier:** L1 · **Type:** knowledge-check · **Kind:** computed · **Points:** 4

## Prompt

<!-- prompt:start -->
**K2.** Why does one GPU running 10 % slow reduce the throughput of a 256-GPU synchronous training
job by about 10 %, rather than by 10 %/256?
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your worked answer: formula, substitution, result with units and evidence label

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
