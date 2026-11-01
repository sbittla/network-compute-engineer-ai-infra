# 20.1.7 — Comparing against the node's own baseline median: worked answer

**Relies on:** manuscript Section 20.7.4 (noise arithmetic) and the lab plants of the answer key
(Part 2, plant B) `[SIMULATED]`.

## Model answer

**Against a fleet-wide threshold:** node-to-node variation in pair-test bandwidth can be larger than the
regression you want to detect. A fixed fleet threshold set for the slowest healthy node misses a 5 %
regression on a fast node; set for the fast nodes, it false-aborts on a slow but healthy one. Comparing each
node with *its own* baseline removes the between-node spread from the test.

**Against a per-sample minimum:** a `min` (or `max`) over samples turns any transient into an abort. In the
lab, `orion-n09` in wave 1 has one post-change sample about 7 % below baseline; its median is within 5 %. A
min-based check aborts a good change, and repeated false aborts teach operators to override the controller.

**Why the median works:** with per-rail busbw noise of about 0.25 GB/s around 44 GB/s `[SIMULATED]`, the
standard error of a 12-sample median is about 1.25 × 0.25 / √12 ≈ 0.09 GB/s, and of the 6-sample baseline
median about 1.25 × 0.25 / √6 ≈ 0.13 GB/s. The difference has a standard error of
√(0.09² + 0.13²) ≈ 0.16 GB/s. A 5 % threshold is 0.05 × 44 = 2.2 GB/s, about 14 standard errors from zero:
it essentially never fires on noise, yet the −9.8 % regression on `orion-n25` (43.67 → 39.41 GB/s) trips it
clearly. Hard-fault counters (Xid, link flaps) are the exception: there, any count above zero is
informative, and a sum or max is right.

## Marking notes (3 points)

1 point for the between-node spread argument; 1 point for the transient-dip argument (the `orion-n09`
example or equivalent); 1 point for the robustness/noise argument for medians.

**Common wrong answers.** "The median is more accurate" without saying what it is robust to. Recommending a
mean: a single deep dip still drags a 12-sample mean.
