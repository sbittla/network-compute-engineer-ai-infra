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

## Before you start

- **Chapter:** Chapter 15 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
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
