# 13.13 — One slow node in a TP job (★★★, L1)

Type: troubleshooting · Kind: written

## Prompt

<!-- prompt:start -->
**13.13 ★★★ L1 — One slow node in a TP job.** A W-TRAIN-shaped job (TP 8) slows by 12 %. Per-rank
logs show that all eight ranks on `orion-n09` have TP communication time 3× the median; their compute,
clocks, and tokens are normal; DP and PP times are normal everywhere; the node was rebooted for a
driver update the previous evening. Rank hypotheses, name discriminating tests (commands and expected
output), give the most likely root cause, the safe fix, and validation evidence.
*Evidence required:* ≥ 3 ranked hypotheses, tests, root cause, fix, validation.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/incident_analysis.md`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
