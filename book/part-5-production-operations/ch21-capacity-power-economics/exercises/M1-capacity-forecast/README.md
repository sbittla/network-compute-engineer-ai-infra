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

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/forecast_p50.csv`
- `outputs/forecast_p90.csv`
- `outputs/answer.md`

Run:

```bash
python solve.py --out outputs/     # your own script; show every formula and substitution
```
