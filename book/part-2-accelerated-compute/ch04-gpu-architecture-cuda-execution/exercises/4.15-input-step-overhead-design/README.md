# Exercise 4.15 — Input and step-overhead strategy for HX8

★★★ · Tier L1 · design challenge · kind: `computed`

<!-- prompt:start -->
**4.15** ★★★ L1 — Design the input and step-overhead strategy for a job using all eight GPUs of an HX8
node (one rank per GPU): each rank consumes 100 MiB of input per step, target step time is 60 ms, the
optimizer touches 1,400 parameter tensors (1,200 of them under 64 K elements), and shapes are static.
Decide: pinned-memory strategy and total pinned budget; where loader worker processes run (NUMA, see
Chapter 3 and Figure R.1, the HX8 host topology in `docs/REFERENCE_CLUSTER.md` Section 1); how copies overlap compute; how to remove optimizer launch overhead (foreach,
fused, CUDA Graphs or `torch.compile`) — and defend each choice against one alternative. State how you
would prove the design works.
*Evidence required:* a one-page design with PCIe budget arithmetic, pinned-memory budget, NUMA placement,
the overhead strategy with a rejected alternative, and a validation plan.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
