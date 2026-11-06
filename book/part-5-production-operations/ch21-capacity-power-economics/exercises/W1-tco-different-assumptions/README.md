# W1 — TCO under different assumptions (★★, L1)

Type: Worked problem · Kind: `computed` · Points: 9

## Prompt

<!-- prompt:start -->
**W1 ★★ L1 — TCO under different assumptions.** Recompute ORION-256's TCO (Section 21.4) with 5-year
amortization, PUE 1.25, electricity $0.12/kWh, allocation 0.80 (replacing the ladder's 0.85 allocation factor; the 0.850
usable fraction is unchanged), and goodput 0.90 (other inputs
unchanged). Report the annual total and the cost per nominal and per useful GPU-hour.
*Evidence required:* every component with formula; the two unit costs.
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
