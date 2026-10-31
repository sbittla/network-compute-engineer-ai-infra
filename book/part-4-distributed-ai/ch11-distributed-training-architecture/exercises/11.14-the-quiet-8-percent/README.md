# 11.14 — The quiet 8 % (★★★, L1)

**Type:** Troubleshooting case · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
**11.14 ★★★ L1 — The quiet 8 %.** After a firmware maintenance window, W-TRAIN's step time is
18.8 s p50 (baseline 17.45 s). Per-rank logs show: ranks 0–255 compute 13.9–14.0 s except ranks 96–103
at 15.2 s; DP comm unchanged; TP comm unchanged on all nodes; every rank except 96–103 shows
≈ 1.3 s more "pp_wait" or collective wait than baseline. `nvidia-smi -q -d PERFORMANCE` on `orion-n13`, the node
hosting ranks 96–103, shows `SW Power Cap: Active`. Walk the diagnostic loop: rank hypotheses, name
discriminating tests, identify the root cause, propose a safe fix and the validation evidence.
*Evidence required:* ranked hypotheses (≥ 3), tests with expected outcomes, root cause, fix,
validation criteria, and an estimate of GPU-hours lost per day.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
