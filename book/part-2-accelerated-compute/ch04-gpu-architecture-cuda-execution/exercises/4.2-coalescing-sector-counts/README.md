# Exercise 4.2 — Coalescing and 32-byte sectors

★ · Tier L1 · knowledge check · kind: `computed`

<!-- prompt:start -->
**4.2** ★ L1 — Thirty-two threads of a warp each load one 4-byte float. How many 32-byte sectors are
fetched when the addresses are (a) consecutive, (b) stride 2 elements, (c) stride 32 elements? What
fraction of fetched bytes is useful in each case?
*Evidence required:* sector counts and useful-byte fractions with arithmetic.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
