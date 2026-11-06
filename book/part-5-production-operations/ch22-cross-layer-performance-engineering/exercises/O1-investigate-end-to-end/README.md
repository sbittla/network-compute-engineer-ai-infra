# O1 — Investigate an end-to-end workload regression (★★, L1)

Outline-mandated · difficulty ★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**O1 ★★ (L1) — Investigate an end-to-end workload regression using supplied GPU, CPU, network,
storage, and scheduler metrics.** Using the lab bundle:
a. Complete lab tasks 1–7.
b. For each inferred cause, cite one *direct* measurement from `node_metrics.csv`, `node_inventory.csv`,
   or `nccl_init_sample.log` (GPU, CPU, network, or storage layer) that corroborates it, with numbers.
c. Fit the model again with a `tp_split × driver_new` and a `tp_split × storage_new` interaction term.
   Report the coefficients and state whether the additive attribution is defensible.
*Evidence required:* checker output; a corroboration table (cause × direct evidence × values);
interaction coefficients with a one-sentence judgment.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 22 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Numbers in prompts are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/check.txt`
- `outputs/corroboration.md`
- `outputs/interactions.md`

Run:

```bash
python ../../lab/check.py > outputs/check.txt
```

### How to fit the interaction terms (part c)

The model already contains one interaction: `TERMS = FACTORS + ["tp_x_storage"]` (line 26 of
`lab/starter/regression_lab.py`), and `job_factor_table` builds `tp_x_storage = tp_split * storage_new`.
Part (c) adds the second one, `tp_split × driver_new`. Do not edit the starter (the lab checker imports
it). Once lab tasks 1–7 pass, add the column and override `TERMS` from a small script in `outputs/`, run
from this folder:

```python
# outputs/interactions.py  (run: python outputs/interactions.py)
import sys
from pathlib import Path
sys.path.insert(0, "../../lab/starter")
import regression_lab as rl

ft = rl.job_factor_table(rl.load_bundle(Path("../../lab/data")))
ft["tp_x_driver"] = ft["tp_split"] * ft["driver_new"]
rl.TERMS = list(rl.TERMS) + ["tp_x_driver"]   # _design() reads TERMS
print(rl.estimate_effects(ft))
```

Report both interaction coefficients with their standard errors (`se_hc3` as well as `se`) in
`outputs/interactions.md`.
