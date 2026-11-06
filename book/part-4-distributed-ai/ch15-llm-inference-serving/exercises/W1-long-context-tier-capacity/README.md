# W1 — Capacity of an alternative layout (★★, L1)

Type: worked-problem · Kind: computed

## Prompt

<!-- prompt:start -->
**W1. ★★ L1 — Capacity of an alternative layout.** Halcyon AI considers a long-context tier: one
TP = 8 replica per HX8 with **FP8 weights (70 GB) and FP8 KV cache**, `memory_fraction` 0.90,
2 GB reserve per GPU, 16-token blocks.
(a) Compute the KV budget, the number of blocks, and the maximum number of concurrent 8,192-token
sequences. (b) Repeat with BF16 KV. (c) Compute the decode-step lower bound and the planning value
(efficiency 0.70, overhead 3 ms) at B = 64 with an average context of 6,000 tokens (FP8 KV), and
the resulting tokens/s.
*Evidence required:* every formula, substituted values and results with units. Lab Part A
functions may be used to check your arithmetic.
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
