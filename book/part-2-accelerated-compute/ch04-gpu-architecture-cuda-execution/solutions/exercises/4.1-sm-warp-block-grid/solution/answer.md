# 4.1 — SM, warp, thread block and grid (model answer)

Relies on manuscript Section 4.3 ("Hierarchy") and Table 4.1. All values `[VENDOR-SPEC, 2026-10]`.

**Definitions (one sentence each).**

- **SM (streaming multiprocessor):** the GPU's replicated compute unit (132 on an ORION H100-SXM-class
  GPU), each with its own warp schedulers, register file (65,536 × 32-bit), shared memory/L1 and Tensor Cores.
- **Warp:** a group of 32 threads that the SM scheduler issues together, one instruction at a time, in
  SIMT fashion; divergent lanes are masked off, not issued separately.
- **Thread block (CTA):** up to 1,024 threads that are guaranteed to run on one SM at the same time, and
  can therefore share shared memory and synchronize with block-level barriers (`__syncthreads()`).
- **Grid:** all the thread blocks of one kernel launch; blocks of a grid cannot assume any execution order
  relative to each other.

**(a) Unit of placement on hardware: the thread block.** The block scheduler assigns each block to one SM
for its whole lifetime; a block never migrates or splits across SMs. This is why occupancy is computed in
whole blocks (Section 4.7).

**(b) Unit of instruction issue: the warp.** Each cycle a scheduler picks one eligible warp and issues its
next instruction for all 32 lanes.

**Common wrong answers.**

- "The thread is the unit of issue." Threads have their own registers and program counter state, but the
  hardware issues per warp; a lone active thread still costs a full warp issue slot.
- "The grid is placed on the GPU." A grid is a software construct; only blocks are placed.
- Confusing the SM with a CUDA core: a CUDA core is one FP32 lane inside an SM sub-partition.
