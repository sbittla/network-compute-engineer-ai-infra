# 12.11 — Analyze an NCCL result set across message sizes (★★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 12

## Prompt

<!-- prompt:start -->
**12.11 (O2) ★★ L1 — Analyze an NCCL result set across message sizes.** Using your lab
implementation (or by hand), analyze all six configurations in `lab/data/`. For each, identify the
latency-dominated and bandwidth-dominated regions (size ranges), fit α and B, compute n½, and state
the plateau busbw. Then write the scaling analysis: how plateau busbw and α change from 1 to 8 nodes,
and what that says about the fabric.
*Evidence required:* a summary table (six rows), region boundaries, a log-log plot of time vs size
for c2 and c5 (matplotlib), and a 150-word scaling verdict.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); the lab data is in [lab/data/](../../lab/data/).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: summary table, region boundaries, 150-word scaling verdict
- `outputs/time_vs_size_c2_c5.png`: log-log plot of time vs size for c2 and c5 (matplotlib), axes labelled with units

Label the data `[SIMULATED]` and fitted values `[MODELED]`; state your region thresholds.
