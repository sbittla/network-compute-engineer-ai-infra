# M2 · Compatibility matrix and staged upgrade plan (★★★ · L1)

Type: outline-mandated · Kind: computed · Points: 25

<!-- prompt:start -->
**M2 ★★★ (L1) [Outline] — Compatibility matrix and staged upgrade plan.** Using
`lab/data/compat_matrix.yaml` as a starting point, (a) extend the matrix with the components it
omits (fabric manager, CUDA user-mode, DCGM, NVIDIA container toolkit, NVMe firmware, PSU firmware)
and state the coupling rule for each; (b) write the staged upgrade plan from B-2026.04 to B-2026.10
for the 32 ORION nodes: qualification, canary (size, placement, bake time with a detection-probability
calculation), wave sizes and per-rack caps, maintenance windows aligned with W-TRAIN checkpoints,
pre-declared abort conditions with thresholds, a per-component rollback table (including at least
one non-reversible component), and the audit evidence you will keep.
*Evidence required:* the extended matrix; the plan with every number derived; the rollback table;
the abort-condition list; the evidence list.
<!-- prompt:end -->

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, plus the evidence label. If you check the arithmetic with a script, save it as
`outputs/work.py` and run it from this folder with `python outputs/work.py`.
