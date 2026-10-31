# O1 — Memory demand vs batch, sequence length and concurrency (★★, L1)

Type: outline-mandated · Kind: computed

## Prompt

<!-- prompt:start -->
**O1. ★★ L1 — Memory demand vs batch, sequence length and concurrency.** Using Lab Part A, fill
in a table of total memory demand (weights + KV) for T-tp4-fp8 at batch 16, 64 and 128 and
sequence lengths 1k, 4k and 16k. Mark every cell that exceeds the 288 GB usable HBM, and state
the maximum concurrent sequences per sequence length. Explain in two sentences which variable
dominates as context grows.
*Evidence required:* the 3 × 3 table, the max-sequence row, and the explanation.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
