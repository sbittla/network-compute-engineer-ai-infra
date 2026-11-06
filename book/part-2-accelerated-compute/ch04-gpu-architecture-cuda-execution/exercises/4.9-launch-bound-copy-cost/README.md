# Exercise 4.9 — Launch-bound loop and copy cost

★★ · Tier L1 · worked problem · kind: `computed`

<!-- prompt:start -->
**4.9** ★★ L1 — *Launch-bound loop and copy cost.* An inference loop issues 400 kernels per iteration
with an average GPU duration of 6 µs; the CPU spends 10 µs per launch (API + framework). Each iteration
also needs a 256 MiB input.
(a) Iteration time and GPU kernel-busy fraction in eager mode.
(b) Iteration time if the 400 kernels are captured in one CUDA Graph (one replay ≈ 15 µs of CPU, ≈ 1 µs
between kernels on the GPU).
(c) Copy time for the input from pageable memory at 12 GB/s versus pinned at 50 GB/s, and the
critical-path cost of each if the pinned copy is prefetched on a side stream during the previous iteration.
*Evidence required:* three results with formulas and units; label `[MODELED]`.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/4.9-launch-bound-copy-cost/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
