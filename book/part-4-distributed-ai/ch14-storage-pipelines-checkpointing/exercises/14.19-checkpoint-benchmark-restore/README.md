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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/manifest.yaml`
- `outputs/results.md`
- `outputs/restore_test.log`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.

On a single GPU host you can produce all three deliverables with
`python scripts/hw_labs.py run ch14 --device gpu` (CPU fallback with `--device cpu`). It writes
`lab/l2/results/<gpu-model>/environment.json` (manifest), `results.json` and `report.md` (results table and
restore test log). Copy or summarize them into `outputs/` and add your own analysis. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.