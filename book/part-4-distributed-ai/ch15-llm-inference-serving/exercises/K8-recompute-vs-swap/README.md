# K8 — Recompute versus swap (★★, L1)

Type: knowledge-check · Kind: computed

## Prompt

<!-- prompt:start -->
**K8. ★★ L1 — Recompute vs swap.** For a preempted 10k-token sequence on a TP = 2 FP8 replica,
estimate the cost of recompute vs swap.
*Evidence required:* both estimates with stated assumptions (prefill µs/token; PCIe GB/s).
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
