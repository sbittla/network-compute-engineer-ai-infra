# W2 — Checkpoint interval and goodput (★★, L1)

Worked problem · difficulty ★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**W2 ★★ L1 — Checkpoint interval and goodput.** For a 256-GPU W-TRAIN job, assume a blocking
checkpoint cost δ = 60 s, the canonical restart cost R = 900 s, and — as a deliberate pessimistic
*variation* on the canonical 48 h (= 1,536 node-h / 32 nodes) — a mean time between job-interrupting
failures M = 24 h `[ILLUSTRATIVE]` (node MTBF halved to 768 h).

1. Compute Young's interval τ and the three waste terms δ/τ, τ/(2M) and R/M.
2. Compute expected lost GPU-hours per failure.
3. If all other goodput losses (scheduling gaps, maintenance, stragglers) total 5 %, how long does
   the 2 × 10¹² token run take, given an ideal duration of 96.00 days?
4. Which single change would you put first in the backlog, and why?

*Evidence required:* arithmetic for each part; the backlog choice justified by numbers.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solve.py --out outputs   # optional: script your arithmetic
```
