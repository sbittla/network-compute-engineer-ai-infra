# 12.9 — Buckets and the alpha-beta model (★★, L1)

**Type:** Worked problem · **Kind:** computed · **Points:** 6

## Prompt

<!-- prompt:start -->
**12.9 ★★ L1 — Buckets and the alpha-beta model.** For a 64-rank all-reduce with α = 47 µs and
B = 346 GB/s (busbw), compute: (a) the time for 4 MB, 25 MB, and 256 MB; (b) n½; (c) the total time to
reduce 4.375 GB as 25 MB buckets versus one message, and explain the difference in terms of α.
*Evidence required:* all values with formulas.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units and evidence labels
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
