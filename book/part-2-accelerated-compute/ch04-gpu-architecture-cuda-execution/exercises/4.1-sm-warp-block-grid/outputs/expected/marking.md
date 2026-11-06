# Marking scheme: 4.1 SM, warp, thread block and grid

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** four one-sentence definitions and the two answers.

| Criterion | Points |
|---|---|
| SM defined as the replicated compute unit with its own warp schedulers, register file, shared memory/L1 and Tensor Cores | 1 |
| Warp defined as 32 threads issued one instruction at a time (SIMT) | 1 |
| Thread block (CTA, up to 1,024 threads, resident on one SM, shares shared memory and barriers) and grid (all blocks of one launch) defined | 1 |
| (a) Unit of placement on hardware is the thread block | 1 |
| (b) Unit of instruction issue is the warp (not the thread) | 1 |
