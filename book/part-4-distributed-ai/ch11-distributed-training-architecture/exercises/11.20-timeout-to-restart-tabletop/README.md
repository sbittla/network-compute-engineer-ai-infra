# 11.20 — From timeout to restart (★★★, L1)

**Type:** Troubleshooting case · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
**11.20 ★★★ L1 — From timeout to restart.** A 512-node W-TRAIN-class job logs an NCCL watchdog timeout
at 03:12. In the preceding 20 minutes: node `orionxl-n312` logged a GPU uncorrectable ECC event (Xid 48-class)
on GPU 5 at 02:58; NIC 2 of `orionxl-n141` logged 14 link-down/up events since 01:00; and the job's step
time on ranks of `orionxl-n141` rose 6 % at 01:05. Using the rank-to-hardware mapping rule of Section 11.8
(TP fastest, 8 ranks per node; the job's node list is `orionxl-n[001-512]` in rank order, so node
`orionxl-nNNN` hosts global ranks 8(NNN − 1) … 8(NNN − 1) + 7), identify the global ranks involved, decide which component most
likely caused the timeout and which is a correlated-but-separate problem, choose the smallest failure
domain to quarantine for each, and write the restart plan (checkpoint choice, replacement nodes,
validation). Distinguish proven cause from correlation.
*Evidence required:* timeline, rank-to-hardware table, health decision per component, restart plan,
and one sentence on what evidence would *prove* the cause.
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
