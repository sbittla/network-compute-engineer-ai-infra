# K5 — Why the model needs a period indicator (★★, L1)

Knowledge check · difficulty ★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**K5 ★★ (L1).** Why does the attribution model include a period indicator (`after`) in addition to the
change-specific factors? What would go wrong without it?
*Evidence required:* the role of the term; a concrete misattribution it prevents.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 22 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Numbers in prompts are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python ../../lab/starter/regression_lab.py --report outputs/report.md   # then refit without `after`
```

### How to refit without `after`

The model terms come from the module-level list `TERMS` in `lab/starter/regression_lab.py` (line 26:
`TERMS = FACTORS + ["tp_x_storage"]`), and `_design()` builds the OLS matrix from it. Once you have
completed `job_factor_table` and `estimate_effects`, do not edit the starter (the lab checker imports
it). Override `TERMS` from a small script in `outputs/` instead, run from this folder:

```python
# outputs/refit_no_after.py  (run: python outputs/refit_no_after.py)
import sys
from pathlib import Path
sys.path.insert(0, "../../lab/starter")
import regression_lab as rl

ft = rl.job_factor_table(rl.load_bundle(Path("../../lab/data")))
with_after = rl.estimate_effects(ft)
rl.TERMS = [t for t in rl.TERMS if t != "after"]   # drop the period indicator
without_after = rl.estimate_effects(ft)
print(with_after, without_after, sep="\n")
```

Compare the `driver_new`, `storage_new`, `tp_split` and `alert_node` coefficients across the two fits.
