# 14.20 — Per-directory create limit (★★, L1)

Type: worked-problem · Kind: computed

## Prompt

<!-- prompt:start -->
**14.20 Per-directory create limit** ★★ · L1
Section 14.14's new trainer image writes 1,025 files per rank from 256 ranks into one checkpoint
directory. Assume the metadata service sustains ≈ 2,700 creates/s into a single directory (the measured
per-directory ceiling) and ≈ 30,000 creates/s in aggregate when the creates are spread
over many directories `[ILLUSTRATIVE]`. Compute the create time per checkpoint (a) in one directory,
(b) with one subdirectory per rank, and (c) with the old format of 2 files per rank in one directory.
(d) What is the largest number of files per rank, written into one directory, that keeps the creates
under 5 % of the asynchronous completion latency L = 18.49 s (Section 14.12)? (e) Which fix would you
take to the Storage team first, and why?
*Evidence required:* each formula with values substituted, times in seconds to three significant
figures, the integer answer to (d), and a one-paragraph recommendation.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 14 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
