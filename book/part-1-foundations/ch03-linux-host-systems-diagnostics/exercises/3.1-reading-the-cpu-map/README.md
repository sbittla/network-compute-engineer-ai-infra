# Exercise 3.1 — Reading the CPU map

**Difficulty:** ★ · **Tier:** L1 · **Type:** knowledge-check · **Kind:** computed · **Points:** 4

## Prompt

<!-- prompt:start -->
On an `HX8`, `lscpu` reports `NUMA node0 CPU(s): 0-55,112-167`. (a) Which logical CPUs are SMT
siblings of physical cores on socket 1? (b) A launcher binds rank 2 (GPU 2) with `taskset -c 56-63`.
What is wrong with that, given Figure 3.1?
*Evidence required:* CPU lists, and one sentence that names the socket of GPU 2 and the consequence.
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
