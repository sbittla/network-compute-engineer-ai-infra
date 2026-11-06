# K6 — 2N feeds (★★, L1)

Type: Knowledge check · Kind: `computed` · Points: 6

## Prompt

<!-- prompt:start -->
**K6 ★★ L1 — 2N feeds.** (a) An ORION rack has A and B sides of two canonical circuits each (32.78 kW
continuous per circuit, 65.55 kW per side). What is the maximum planned rack load with a 10 % transient
margin, and why? (b) Repeat for a legacy rack with one circuit per side.
*Evidence required:* two numbers and the failure scenario that sets them.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Inputs are `[ILLUSTRATIVE]` and results `[MODELED]` unless stated.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
