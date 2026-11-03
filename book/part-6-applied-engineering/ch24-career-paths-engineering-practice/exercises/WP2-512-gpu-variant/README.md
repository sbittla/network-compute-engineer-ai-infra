# WP2 — A 512-GPU variant (★★★, L1)

Worked problem · difficulty ★★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**WP2 ★★★ L1 — A 512-GPU variant.** Halcyon AI considers a 512-GPU (64 × HX8) cluster with the same
64-port 400G switches, rail-optimized and non-blocking.
(a) Size it: leaves per rail, total leaves, spines, links per leaf–spine pair, total links.
(b) If 32 equal RoCE flows leave a leaf on 32 uplinks with random ECMP hashing, how many uplinks are
idle on average? Recompute with 4 queue pairs per connection (128 flows of one quarter the size each).
(c) For W-TRAIN on ORION-256, recompute Young's checkpoint interval and the total overhead if the
node MTBF halves from the canonical 1,536 h to 768 h (blocking checkpoint
cost δ = 60 s as in Section 24.6 and Chapter 23, restart 900 s).
*Evidence required:* every formula with substituted values and units; results labelled `[MODELED]`.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python outputs/work.py   # optional: your own script, if you script the arithmetic
```
