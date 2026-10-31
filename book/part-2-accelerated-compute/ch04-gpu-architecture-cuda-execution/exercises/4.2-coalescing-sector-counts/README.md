# Exercise 4.2 — Coalescing and 32-byte sectors

★ · Tier L1 · knowledge check · kind: `computed`

<!-- prompt:start -->
**4.2** ★ L1 — Thirty-two threads of a warp each load one 4-byte float. How many 32-byte sectors are
fetched when the addresses are (a) consecutive, (b) stride 2 elements, (c) stride 32 elements? What
fraction of fetched bytes is useful in each case?
*Evidence required:* sector counts and useful-byte fractions with arithmetic.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/
```
