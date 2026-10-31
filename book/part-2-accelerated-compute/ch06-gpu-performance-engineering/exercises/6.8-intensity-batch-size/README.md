# Exercise 6.8 — Intensity and batch size

★★ · Tier L1 · worked problem · kind: `computed`

<!-- prompt:start -->
**6.8** ★★ L1 — *Intensity and batch size.* For a BF16 linear layer with *K* = *N* = 4,096: (a) for *M* =
4,096 tokens compute *W*, minimum *Q*, *I*, the bound and the time at roof; (b) repeat for *M* = 64;
(c) find the smallest *M* for which the layer is compute-bound on ORION. *Evidence required:* all
arithmetic; label `[MODELED]`.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/
```
