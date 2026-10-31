# W1 — TCO under different assumptions (★★, L1)

Type: Worked problem · Kind: `computed` · Points: 9

## Prompt

<!-- prompt:start -->
**W1 ★★ L1 — TCO under different assumptions.** Recompute ORION-256's TCO (Section 21.4) with 5-year
amortization, PUE 1.25, electricity $0.12/kWh, allocation 0.80, and goodput 0.90 (other inputs
unchanged). Report the annual total and the cost per nominal and per useful GPU-hour.
*Evidence required:* every component with formula; the two unit costs.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`

Run:

```bash
python solve.py --out outputs/     # your own script; show every formula and substitution
```
