# O3 — Compare two serving configurations (★★, L1)

Type: outline-mandated · Kind: computed

## Prompt

<!-- prompt:start -->
**O3. ★★ L1 — Compare two serving configurations.** Using Lab Part A's `compare_serving_configs`,
recommend one configuration for a latency-sensitive objective and another for a
throughput-oriented objective. Then name the operating condition (load, context length, or SLO)
under which each recommendation would flip.
*Evidence required:* the comparison table, both recommendations with numbers, and the flip
conditions.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
