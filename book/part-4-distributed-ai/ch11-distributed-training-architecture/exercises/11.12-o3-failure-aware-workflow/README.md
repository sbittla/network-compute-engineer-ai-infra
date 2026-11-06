# 11.12 — Failure-aware training workflow (★★★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 20

## Prompt

<!-- prompt:start -->
**11.12 (O3) ★★★ L1 — Failure-aware training workflow.** Design the checkpoint-and-restart workflow
for W-TRAIN on (a) ORION-256 and (b) ORION-XL (4,096 GPUs), using the canonical job MTBF of 48 h (ORION-256, 32 nodes) and
3 h (ORION-XL, 512 nodes), i.e. 1,536 node-hours ÷ node count, C = 45 s (synchronous) or 5 s (asynchronous), and R = 900 s. Give τ_opt, expected waste, expected lost work
per failure in GPU-hours, and lost GPU-hours per day. Then state the restart procedure (detection,
isolation, replacement, restore, validation) and the retry/quarantine policy, and say which term
(C, R, or MTBF) you would invest in at each scale.
*Evidence required:* a table of the eight numbers per scenario, a state diagram or numbered
procedure, and an investment recommendation justified by the numbers.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) with W-TRAIN on ORION-256 and the assumptions in Table 11.4.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/11.12-o3-failure-aware-workflow/` (instructor material in the full repository; removed from student releases).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
