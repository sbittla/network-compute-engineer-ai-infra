# Exercise K3 — Bandwidth unit conversions

**Difficulty:** ★ · **Tier:** L1 · **Type:** knowledge-check · **Kind:** computed · **Points:** 4

## Prompt

<!-- prompt:start -->
**K3.** Convert: (a) 400 Gb/s to GB/s; (b) NVLink "900 GB/s" for an ORION GPU into a per-direction
figure; (c) a node's total backend bandwidth into GB/s per direction.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 1 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your worked answer: formula, substitution, result with units and evidence label

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
