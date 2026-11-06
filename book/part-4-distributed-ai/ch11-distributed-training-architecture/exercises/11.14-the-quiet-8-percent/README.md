# 11.14 — The quiet 8 % (★★★, L1)

**Type:** Troubleshooting case · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
**11.14 ★★★ L1 — The quiet 8 %.** After a firmware maintenance window, W-TRAIN's step time is
18.8 s p50 (baseline 17.45 s). Per-rank logs show: ranks 0–255 compute 13.9–14.0 s except ranks 96–103
at 15.2 s; DP comm unchanged; TP comm unchanged on all nodes; every rank except 96–103 shows
≈ 1.3 s more "pp_wait" or collective wait than baseline. `nvidia-smi -q -d PERFORMANCE` on `orion-n13`, the node
hosting ranks 96–103, shows `SW Power Cap: Active`; so do peer nodes, intermittently, under the same
load. Walk the diagnostic loop: rank hypotheses, name
discriminating tests, identify the root cause, propose a safe fix and the validation evidence.
*Evidence required:* ranked hypotheses (≥ 3), tests with expected outcomes, root cause, fix,
validation criteria, and an estimate of GPU-hours lost per day.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 11 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
