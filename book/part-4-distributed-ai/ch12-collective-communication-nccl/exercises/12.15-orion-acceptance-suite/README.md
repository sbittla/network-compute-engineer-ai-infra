# 12.15 — ORION collective acceptance suite (★★★, L1)

**Type:** Design challenge · **Kind:** written · **Points:** 15

## Prompt

<!-- prompt:start -->
**12.15 ★★★ L1 — ORION collective acceptance suite.** Design the nccl-tests acceptance suite that
Fleet runs before a node joins the training partition and nightly on idle nodes. Cover: which
collectives, which communicator shapes (single node, two-node pairs, rail-pinned one-GPU-per-node,
full 8-node), size ranges, repetitions, pass/fail thresholds with the statistic used, run time budget,
artifacts recorded, and safety constraints. Defend one trade-off (coverage vs time vs fabric impact).
*Evidence required:* the suite as a table, thresholds tied to Table 12.7 baselines, and a
one-paragraph defence.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Show every formula, substitution and result with units, and label each number with its evidence label.
