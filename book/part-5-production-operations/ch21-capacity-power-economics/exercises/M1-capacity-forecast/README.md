# M1 — Capacity forecast (★★, L1)

Type: Outline-mandated · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
**M1 ★★ L1 — Capacity forecast.** Build a capacity forecast from **accelerator supply, workload demand,
utilization, maintenance reserve, and expected growth** (lab Tasks 1–2) and extend it with a p90 demand
scenario (+25 % demand from 2028Q3). Report the first shortfall quarter and order-by dates for each
scenario.
*Evidence required:* forecast table for both scenarios; order-by dates; the binding resource per shortfall.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 21 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Inputs are `[ILLUSTRATIVE]` and results `[MODELED]` unless stated.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/forecast_p50.csv`
- `outputs/forecast_p90.csv`
- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
