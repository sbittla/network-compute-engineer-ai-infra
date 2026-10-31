# 14.19 — Checkpoint benchmark and restore test (★★, L2)

Type: outline-mandated · Kind: written

## Prompt

<!-- prompt:start -->
**14.19 Checkpoint benchmark and restore test** ★★ · L2 **(outline)**
On one GPU host with PyTorch 2.x, checkpoint a model of ≥ 1 GB of state with
`torch.distributed.checkpoint.save` and with `async_save` (verify the API for your version). Measure,
over ≥ 5 repetitions after one warm-up: blocking time, completion time, step time before/during/
after, and peak pinned host memory. Then corrupt a copy of one data file (on a scratch copy only),
show that a checksum-based validator rejects it, restore from the intact copy, and show that the
first step's loss matches the value recorded at save within a stated tolerance.
*Evidence required:* environment manifest, a results table with median and spread, and the restore
test log.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/manifest.yaml`
- `outputs/results.md`
- `outputs/restore_test.log`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
