# Exercise 6.20 — Keep run A3: recompute C vs A

★★ · Tier L1 · reflection · kind: `computed`

<!-- prompt:start -->
**6.20** ★★ L1 — Suppose the protocol had no version-mismatch rule, so run A3 (PyTorch 2.3.1) stays in the
baseline. Recompute the C vs A comparison with the lab code and explain why exclusion rules must be
pre-registered and applied symmetrically to every arm.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 6.1 ceilings (989 TFLOP/s dense BF16, 1,979 TFLOP/s FP8, 67 TFLOP/s FP32 SIMT, 3.35 TB/s HBM).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

*Evidence required for 6.16–6.20:* short written answers (≤ 150 words each) citing specific mechanisms or data.

## Turning the version rule off

`clean_runs()` (in `lab/starter/analysis.py`) has no switch for rule (a), and you should not add one
to the lab code. Disable it from the data side instead: overwrite every run's `driver`, `cuda` and
`torch` fields with the reference values in **both** arms, so rule (a) never fires while the clock rule
and everything else still apply symmetrically. With your Lab 6 `compare()` and `noise_floor()`
implemented, from this folder:

```bash
python -c "
import sys, pandas as pd; sys.path.insert(0, '../../lab/starter'); import analysis as a
REF = {'driver': '570.124.06', 'cuda': '12.8', 'torch': '2.4.0'}
load = lambda f: pd.read_csv('../../lab/data/' + f, dtype={'cuda': str})
same_sw = lambda d: d.assign(**REF)          # every run now matches the reference software
base, cand = load('bench_baseline.csv'), load('bench_candidate_c.csv')
floor = a.noise_floor(load('bench_aa.csv'), REF)
for label, b, c in [('with rule', base, cand), ('no version rule', same_sw(base), same_sw(cand))]:
    r = a.compare(b, c, REF, floor)
    print(label, r['point'], r['ci_lo'], r['ci_hi'], r['p_perm'], r['decision'], [e['run_id'] for e in r['excluded']])
"
```

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
