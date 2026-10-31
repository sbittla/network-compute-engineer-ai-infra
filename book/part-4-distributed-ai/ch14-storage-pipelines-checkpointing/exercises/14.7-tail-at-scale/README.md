# 14.7 — Tail at scale (★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**14.7 Tail at scale** ★ · L1
256 ranks each issue one storage read per step and the step waits for all of them. What fraction of
steps sees at least one read slower than the per-read p99? The p99.9? What happens to these numbers
at 4,096 ranks? *Evidence required:* the expression 1 − q^N, values to two significant figures.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
