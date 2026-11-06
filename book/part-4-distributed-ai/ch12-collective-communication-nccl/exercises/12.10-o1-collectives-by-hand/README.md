# 12.10 — Collectives by hand (★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
**12.10 (O1) ★ L1 — Collectives by hand.** Three ranks hold R0 = [2, 4, 6], R1 = [1, 3, 5],
R2 = [10, 20, 30]. Give the result on every rank of: all-reduce (sum), reduce (sum, root R0),
reduce-scatter (sum; rank *r* keeps element *r*), all-gather (of each rank's first element),
broadcast (root R1), and all-to-all. Then trace a ring all-reduce for this example step by step and
count the bytes each rank sends, assuming 4-byte elements.
*Evidence required:* six results, a step table with 2(n − 1) = 4 steps, and the byte count compared
with 2(n − 1)/n × S.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 12 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units and evidence labels
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
