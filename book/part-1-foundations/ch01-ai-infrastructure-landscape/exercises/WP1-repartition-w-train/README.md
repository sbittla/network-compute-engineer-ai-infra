# Exercise WP1 — Re-partitioning W-TRAIN

**Difficulty:** ★★ · **Tier:** L1 · **Type:** worked-problem · **Kind:** computed · **Points:** 15

## Prompt

<!-- prompt:start -->
Halcyon considers running W-TRAIN as TP = 4, PP = 8, DP = 8 (still 256 GPUs; each TP group occupies
half a node). For one GPU per step, compute: (a) tensor-parallel bytes sent and the NVLink lower
bound; (b) data-parallel bytes sent and the NIC lower bound; (c) pipeline bytes sent by a
middle-stage GPU and the NIC lower bound; (d) compare with the TP = 8, PP = 4 baseline of Table 1.6
and name one cost of the new layout that the ceiling model does not capture.

**Evidence required:** formula → substitution → result for each of (a)–(c), with units; a comparison
table; one named unmodeled cost with a one-sentence mechanism.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: formula, substitution and result for (a) to (c), the comparison table and one unmodeled cost

Command to run (from this folder):

```bash
python outputs/solve.py --out outputs/   # optional: if you script the arithmetic
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
