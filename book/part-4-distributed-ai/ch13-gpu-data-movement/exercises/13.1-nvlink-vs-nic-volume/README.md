# 13.1 — NVLink versus NIC bytes per step (★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**13.1 ★ L1.** Why does NVLink carry roughly 120× more bytes per GPU per step than the NIC for W-TRAIN
on ORION? *Evidence required:* the two volumes from Table 13.1 and the parallelism responsible.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/13.1-nvlink-vs-nic-volume/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`
- `outputs/result.json (optional, from your own script)`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
