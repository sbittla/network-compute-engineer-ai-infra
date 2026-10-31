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

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/
```
