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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/12.15-orion-acceptance-suite/` (instructor material in the full repository; removed from student releases).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: your answer, in the format the evidence line asks for

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`).
