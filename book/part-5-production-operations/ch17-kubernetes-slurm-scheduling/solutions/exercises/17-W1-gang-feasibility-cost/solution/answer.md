# 17-W1 — Gang feasibility and cost

Free GPUs p01–p12 = `[8, 8, 0, 4, 6, 2, 8, 3, 5, 8, 1, 7]`; p07 is `draining`; all rails up.

1. **Naive panel** = 8 + 8 + 0 + 4 + 6 + 2 + 8 + 3 + 5 + 8 + 1 + 7 = **60 GPUs**. p07's 8 are not
   eligible (draining takes no new work), so eligible = 60 − 8 = **52 GPUs**.
2. **Largest gang now.** Multi-node jobs take whole nodes. Whole-free eligible nodes: p01, p02, p10
   (p07 excluded) = 3 → **3 nodes = 24 GPUs**. (Not ⌊52/8⌋ = 6 nodes: free GPUs on partial nodes
   cannot be combined into whole nodes.)
3. **4-node gang (32 GPUs).** Eligible free 52 ≥ 32 but whole nodes 3 < 4 → pending reason
   **Fragmentation** (capacity exists, shape does not), not InsufficientCapacity.
4. **6-GPU single-node job, best fit.** Candidates with ≥ 6 free: p01 (8), p02 (8), p05 (6), p10 (8),
   p12 (7) → leftovers 2, 2, 0, 2, 1 → **p05** (0 left). Socket alignment is not a criterion for
   5–7 GPU jobs (they cannot fit one socket).
5. **Partial-allocation deadlock without gangs.** Two 3-node jobs scheduled pod by pod, interleaved,
   on 4 free nodes: A gets 2 nodes, B gets 2 nodes, each waits for a third → **all 4 × 8 = 32 GPUs
   stranded**. Cost = 32 GPUs × 5 h = **160 GPU-hours**; × $2.50 = **$400** `[ILLUSTRATIVE price]`.
6. **Preemption cost.** Expected lost work = half the checkpoint interval plus restart:
   128 × (45/2 min + 15 min) = 128 × (0.375 h + 0.25 h) = 128 × 0.625 h = **80 GPU-hours** per
   preemption `[MODELED]`.

**Common mistakes:** including the draining node; largest gang = ⌊52/8⌋; using the full 45-minute
interval instead of half; reporting InsufficientCapacity in part 3. Source: Sections 17.4.1, 17.6.
`solve.py` recomputes every part from the free list.
