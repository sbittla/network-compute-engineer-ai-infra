# 14.8 — Checkpoint size, write time and recovery-point exposure (★★, L1)

Type: worked-problem · Kind: computed

## Prompt

<!-- prompt:start -->
**14.8 Checkpoint size, write time, and recovery-point exposure** ★★ · L1 **(outline)**
A 34 × 10⁹-parameter model trains with BF16 mixed precision and Adam (14 B/param checkpointed) on 128
GPUs. The PFS writes 50 GB/s aggregate; assume 80 % efficiency for a full-cluster burst and 1.0 s for
barrier + metadata + commit. The team checkpoints synchronously every 15 minutes of training.
(a) Checkpoint size and per-GPU shard size. (b) Write time and blocking time. (c) Overhead %.
(d) Worst-case RPO and expected lost work per failure. (e) They switch to asynchronous saves with a
0.6 s snapshot and keep the 15-minute interval: what happens to overhead and RPO? (f) What interval
would bring worst-case RPO to ≈ 5 minutes, and what overhead would that cost (assume 3 %
interference while persisting)? *Evidence required:* formula → substitution → result for each part.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
