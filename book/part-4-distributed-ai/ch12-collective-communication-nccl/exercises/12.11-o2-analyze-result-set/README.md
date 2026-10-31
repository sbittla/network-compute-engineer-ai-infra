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

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: summary table, region boundaries, 150-word scaling verdict
- `outputs/time_vs_size_c2_c5.png`: log-log plot of time vs size for c2 and c5 (matplotlib), axes labelled with units

Label the data `[SIMULATED]` and fitted values `[MODELED]`; state your region thresholds.
