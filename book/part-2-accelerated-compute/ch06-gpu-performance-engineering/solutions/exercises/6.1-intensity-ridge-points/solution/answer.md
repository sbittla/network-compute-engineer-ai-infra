# 6.1 — Arithmetic intensity and ridge points (model answer, 3 points)

Relies on manuscript Section 6.2 and Section 6.3 (Table 6.1 ceilings, `[VENDOR-SPEC, 2026-10]`). Values
`[MODELED]`; `solve.py` reads `lab/data/device.yaml` and asserts them.

**Definitions (1 point).**

- *Arithmetic intensity* *I* = FLOPs performed / bytes moved to and from DRAM (FLOP/B), a property of a kernel
  at a given shape.
- *Ridge point* *I*\* = peak compute / peak memory bandwidth = *P* / *B*: the intensity at which the memory roof
  and the compute roof meet. Kernels with *I* < *I*\* are memory-bound; with *I* > *I*\*, compute-bound.

**Ridge values (2 points)**, all against the 3.35 TB/s HBM roof:

| Ceiling | Arithmetic | Ridge |
|---|---|---|
| Dense BF16 (Tensor Cores) | 989 × 10¹² / 3.35 × 10¹² | **≈ 295 FLOP/B** |
| Dense FP8 (Tensor Cores) | 1,979 × 10¹² / 3.35 × 10¹² | **≈ 591 FLOP/B** |
| FP32 SIMT (no Tensor Cores) | 67 × 10¹² / 3.35 × 10¹² | **≈ 20 FLOP/B** |

**Interpretation.** Lower precision moves the ridge to the right: an FP8 GEMM needs twice the intensity of a
BF16 one to be compute-bound. A kernel must always be judged against the ridge of the precision and pipe it
actually uses; Lab 6's FP32 stencil looks "terrible" at 5.8 % of the BF16 roof but runs at 85 % of its own
FP32 roof.

**Common wrong answers.** Using sparse peaks (1,979 / 3,958 TFLOP/s); dividing by bidirectional or L2
bandwidth; omitting units.
