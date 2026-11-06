# Exercise 4.11 — Trace an operation end to end

★ · Tier L1 · outline-mandated · kind: `computed`

<!-- prompt:start -->
**4.11** ★ L1 — *Trace an operation end to end.* For a BF16 matrix multiplication C = A × B with
N = 8,192 (square) on one ORION GPU, where A and B start in pinned host memory and C must return to the
host: (a) draw the sequence of host launch, H2D copies, kernel, D2H copy and synchronization (Mermaid or
ASCII), marking where the CPU waits and where the GPU waits; (b) estimate each stage's time at 52 GB/s
PCIe and 70 % of 989 TFLOP/s `[MODELED]`; (c) propose how a real training job avoids paying (b)'s copy
costs.
*Evidence required:* annotated diagram, three stage times with arithmetic, one-paragraph restructuring.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 4 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
