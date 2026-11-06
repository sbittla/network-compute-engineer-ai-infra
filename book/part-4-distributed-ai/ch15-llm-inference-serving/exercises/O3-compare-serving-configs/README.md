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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
