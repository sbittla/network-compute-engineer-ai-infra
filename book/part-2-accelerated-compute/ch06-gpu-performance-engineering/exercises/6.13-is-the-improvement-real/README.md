# Exercise 6.13 — Is the improvement real?

★★ · Tier L1 · outline-mandated · kind: `computed`

<!-- prompt:start -->
**6.13** ★★ L1 — *Is the improvement real?* Run medians (ms) for an inference kernel: baseline 12.41,
12.37, 12.52, 12.44, 12.39, 12.47; candidate 12.10, 12.22, 12.05, 12.31, 12.95, 12.12. The candidate's
fifth run logged `sw_power_cap` on most iterations. The A/A floor is 0.9 %; the practical threshold is 2 %.
Using the lab's `permutation_test` and `bootstrap_ratio_ci` (seed 11, 4,000 replicates), decide with and without the fifth run
and justify which decision stands. *Evidence required:* medians, relative changes, p-values, bootstrap bands, decisions,
justification.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/
```
