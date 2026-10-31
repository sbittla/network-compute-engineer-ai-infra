# Exercise 3.1 — Reading the CPU map

**Difficulty:** ★ · **Tier:** L1 · **Type:** knowledge-check · **Kind:** computed · **Points:** 4

## Prompt

<!-- prompt:start -->
On an `HX8`, `lscpu` reports `NUMA node0 CPU(s): 0-55,112-167`. (a) Which logical CPUs are SMT
siblings of physical cores on socket 1? (b) A launcher binds rank 2 (GPU 2) with `taskset -c 56-63`.
What is wrong with that, given Figure 3.1?
*Evidence required:* CPU lists, and one sentence that names the socket of GPU 2 and the consequence.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your answer with the evidence the prompt requires

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
