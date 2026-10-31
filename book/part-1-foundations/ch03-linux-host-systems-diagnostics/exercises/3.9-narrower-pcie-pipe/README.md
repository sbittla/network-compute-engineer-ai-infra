# Exercise 3.9 — The price of a narrower pipe

**Difficulty:** ★★ · **Tier:** L1 · **Type:** worked-problem · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
Using the method of Section 3.11 and W-TRAIN's parallelism (TP = 8, PP = 4, DP = 8, BF16 gradients, ring
all-reduce, 45 GB/s achievable on a healthy rail, 82 % PCIe efficiency):
(a) Compute the raw per-direction bandwidth of PCIe Gen5 x16, Gen4 x16, Gen4 x2 and Gen1 x16 (note that
Gen1/Gen2 use 8b/10b encoding).
(b) Rail NIC 4 on one node has trained at Gen4 x16 instead of Gen5 x16. Compute the extra DP all-reduce
time per step (upper bound) and the GPU-hours lost per day across ORION.
(c) ORION-256 has no spare node. Using the decision rule of Section 3.11 Step 6, decide whether to keep
running, shrink to DP = 7, or plan a stop for this fault, and compare with the Gen3 x8 case.
*Evidence required:* formulas, substituted values and results with units, each labelled `[MODELED]`.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your answer with the evidence the prompt requires

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
