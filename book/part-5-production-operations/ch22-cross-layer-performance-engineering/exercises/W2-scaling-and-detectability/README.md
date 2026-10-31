# W2 — Scaling efficiency and detectability (★★, L1)

Worked problem · difficulty ★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**W2 ★★ (L1) — Scaling efficiency and detectability.** W-TRAIN ablations measure median step times of
17.38 s (64 GPUs, DP = 2), 17.62 s (128 GPUs, DP = 4), and 17.90 s (256 GPUs, DP = 8); per-GPU work is
constant.

a. Compute tokens/s and weak-scaling efficiency at 128 and 256 GPUs relative to 64 GPUs.
b. Using the straggler model of Section 22.5.2 with per-node jitter σ = 0.5 s and expected maxima of
   1.42σ (8 nodes), 1.77σ (16 nodes), and 2.07σ (32 nodes), how much of each gap does straggling
   explain? What remains?
c. A vendor proposes an NCCL setting that "saves 0.15 s per step" at 256 GPUs. Run-to-run σ of per-job
   means is 0.11 s. Can 5 runs per arm detect it (MDE at 5 % two-sided, 80 % power)? How many runs per arm
   would you need?

*Evidence required:* formulas, substituted values, results with units; a clear yes/no with n.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python work.py   # optional: script your arithmetic; save the working in outputs/answer.md
```
