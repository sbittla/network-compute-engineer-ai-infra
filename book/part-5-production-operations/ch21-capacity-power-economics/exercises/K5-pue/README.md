# K5 — PUE (★, L1)

Type: Knowledge check · Kind: `computed` · Points: 5

## Prompt

<!-- prompt:start -->
**K5 ★ L1 — PUE.** ORION-256's sustained IT load is 304.6 kW (32 × 8.5 kW × 1.12). What is the facility
power at the canonical PUE 1.25 and at 1.45 (a hot-season variation)? What does PUE not tell you?
*Evidence required:* two results; two limitations.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Inputs are `[ILLUSTRATIVE]` and results `[MODELED]` unless stated.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/K5-pue/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
