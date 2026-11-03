# R2 — The break-even paragraph: model answer

Sources: manuscript Section 21.5 (Table 21.6 and the break-even); `lab/data/designs.yaml`; Exercise M2's
sensitivity table. All numbers `[MODELED]`.

**Model paragraph (memo-ready).**

> Design B wins only because of one input we have not measured: its per-GPU training throughput,
> assumed to be 2.2× an HX8 GPU. Its TCO ($20.48M/yr) and node count (62, power-bound) do not depend
> on that figure, so B's useful units per $M scale linearly with it: 31.49 × (x / 2.2). A delivers
> 26.69 per $M, so B breaks even at x = 2.2 × 26.69 / 31.49 ≈ **1.86×**. At 1.8× B falls to 25.8 per
> $M and A is the better buy. At 2.0× B leads by 7 %. Per facility megawatt the margin is much wider
> (645 vs 396 units), so if power rather than money becomes the constraint B remains preferable down
> to ≈ 1.35× (2.2 × 396 / 645). Before committing, we will run W-TRAIN and the `chat-70b` inference
> load test on a B-class evaluation system using the Chapter 22 method: fixed model and parallelism,
> warm-up excluded, ≥ 5 repetitions, median and p95 step time, and at least one test at a scale that
> crosses the 2:1 spine tier so the 0.93 communication efficiency is measured rather than modeled.
> Decision rule, stated in advance: B if measured throughput ≥ 2.0× (a margin over 1.86× for
> measurement uncertainty); A if ≤ 1.8×; between the two, renegotiate B's price or rerun at production
> scale.

**Why this is the right paragraph.** It names the uncertain input, shows the break-even arithmetic,
states what happens on both sides, adds the per-MW view that matters if power binds, and turns the
uncertainty into an experiment with a pre-declared decision rule.

**Common weaknesses:** quoting 1.86× without derivation; recommending B unconditionally; proposing
a vendor datasheet comparison (peak FLOPs) instead of a workload benchmark.
