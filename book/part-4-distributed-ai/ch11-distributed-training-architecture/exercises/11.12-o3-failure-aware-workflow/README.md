# 11.12 — Failure-aware training workflow (★★★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 20

## Prompt

<!-- prompt:start -->
**11.12 (O3) ★★★ L1 — Failure-aware training workflow.** Design the checkpoint-and-restart workflow
for W-TRAIN on (a) ORION-256 and (b) ORION-XL (4,096 GPUs), using the canonical job MTBF of 48 h and 3 h
(1,536 node-hours / nodes), C = 45 s (synchronous) or 5 s (asynchronous), and R = 900 s. Give τ_opt, expected waste, expected lost work
per failure in GPU-hours, and lost GPU-hours per day. Then state the restart procedure (detection,
isolation, replacement, restore, validation) and the retry/quarantine policy, and say which term
(C, R, or MTBF) you would invest in at each scale.
*Evidence required:* a table of the eight numbers per scenario, a state diagram or numbered
procedure, and an investment recommendation justified by the numbers.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: formula → substitution → result with units, each number labelled `[MODELED]`
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
