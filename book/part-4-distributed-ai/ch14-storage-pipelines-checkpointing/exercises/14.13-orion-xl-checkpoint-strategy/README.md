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

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/orion_xl_inputs.yaml`
- `outputs/planner_table.md`
- `outputs/recommendation.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
