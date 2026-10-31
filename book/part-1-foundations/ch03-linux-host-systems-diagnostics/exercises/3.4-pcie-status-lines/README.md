# Exercise 3.4 — PCIe status lines

**Difficulty:** ★ · **Tier:** L1 · **Type:** knowledge-check · **Kind:** computed · **Points:** 4

## Prompt

<!-- prompt:start -->
Classify each as *fault*, *probably benign — verify*, or *healthy*, and justify:
(a) GPU `LnkCap 32GT/s x16`, `LnkSta 32GT/s x8`, utilization 95 %;
(b) GPU `LnkCap 32GT/s x16`, `LnkSta 2.5GT/s x16`, utilization 0 %;
(c) BMC VGA `LnkCap 5GT/s x1`, `LnkSta 5GT/s x1`;
(d) rail NIC `LnkCap 32GT/s x16`, `LnkSta 16GT/s x16`, captured during an all-reduce benchmark.
*Evidence required:* a verdict per line, with the rule applied.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your answer with the evidence the prompt requires

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
