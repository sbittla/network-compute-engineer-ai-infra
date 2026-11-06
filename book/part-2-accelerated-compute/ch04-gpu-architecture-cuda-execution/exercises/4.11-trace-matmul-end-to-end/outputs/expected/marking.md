# Marking scheme: 4.11 Trace an operation end to end

Type outline-mandated · kind computed · tier L1 · 10 points

**Evidence required:** annotated diagram, three stage times with arithmetic, one-paragraph restructuring.

| Criterion | Points |
|---|---|
| (a) diagram shows launch, two H2D copies, kernel, D2H and final sync; CPU waits only at the final synchronize; GPU SMs wait on H2D; D2H waits on the kernel | 3 |
| (b) H2D 268,435,456 B / 52 GB/s = 5.16 ms; kernel 1.0995e12 FLOP / 692.3 TFLOP/s = 1.59 ms; D2H 2.58 ms; total about 9.33 ms, labelled [MODELED] | 4 |
| (c) restructuring: operands resident in HBM, only small input batches cross PCIe via pinned side-stream prefetch, only scalars read back; intensity vs PCIe ridge argument | 3 |
