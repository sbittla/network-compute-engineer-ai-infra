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

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/check.txt`
- `outputs/corroboration.md`
- `outputs/interactions.md`

Run:

```bash
python ../../lab/check.py > outputs/check.txt
```
