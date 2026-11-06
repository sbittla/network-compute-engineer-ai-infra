# 14.13 — Checkpoint strategy for ORION-XL (★★★, L1)

Type: design-challenge · Kind: computed

## Prompt

<!-- prompt:start -->
**14.13 Checkpoint strategy for ORION-XL** ★★★ · L1 **(outline)**
Halcyon will train a 405 × 10⁹-parameter model on ORION-XL (4,096 GPUs, 512 HX8 nodes) with a 20 s
step. Assume `[ILLUSTRATIVE]`: PFS 400 GB/s write and 800 GB/s read at 75 % efficiency, commit 3 s,
a PFS checkpoint quota of 25 TB, the canonical ORION-XL job MTBF of 3 h (`docs/REFERENCE_CLUSTER.md`),
40 % hard failures; other inputs, including restart components, as in `orion_ckpt_inputs.yaml`. Design a checkpoint strategy that balances checkpoint
overhead, storage capacity, restart time, and failure frequency. Your answer must include the
strategy comparison (from your planner with a modified YAML), the chosen interval, retention policy
that fits the quota, RPO and time-to-resume targets, the PFS burst every other tenant will see, and
the single highest-leverage improvement beyond checkpointing. *Evidence required:* the YAML you used,
the planner table, a capacity calculation, and a one-page defended recommendation.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Planner inputs:** `orion_ckpt_inputs.yaml` is [lab/data/orion_ckpt_inputs.yaml](../../lab/data/orion_ckpt_inputs.yaml), the input file of lab Part A. Copy it to `outputs/` and edit the copy rather than the lab file; "your planner" is your `compare_strategies` from `lab/starter/storage_lab.py` (finish lab Part A first, Exercise 14.11), loaded with the edited YAML.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/orion_xl_inputs.yaml`
- `outputs/planner_table.md`
- `outputs/recommendation.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
