# 4.2 — Coalescing and 32-byte sectors (model answer)

Relies on manuscript Section 4.4 (memory hierarchy, 32-B sectors and coalescing). Values `[MODELED]`;
`solve.py` enumerates the 32 addresses and counts distinct sectors.

**Method.** A warp issues one load instruction for 32 threads. The memory system fetches whole 32-B
sectors; the useful data is always 32 × 4 B = **128 B**. Count the sectors the 32 addresses touch
(assume the base address is 128-B aligned), then useful fraction = 128 B / (sectors × 32 B).

| Case | Address span | Sectors | Bytes fetched | Useful fraction |
|---|---|---|---|---|
| (a) consecutive | 32 × 4 B = 128 B | 128 / 32 = **4** | 128 B | 128 / 128 = **100 %** |
| (b) stride 2 elements (8 B apart) | 32 × 8 B = 256 B | 256 / 32 = **8** | 256 B | 128 / 256 = **50 %** |
| (c) stride 32 elements (128 B apart) | each thread in its own sector | **32** | 32 × 32 B = 1,024 B | 128 / 1,024 = **12.5 %** |

**Interpretation.** In (b) every sector holds 4 useful bytes out of 8 B fetched per element pair; in (c)
each 32-B sector delivers one 4-B value. A memory-bound kernel with pattern (c) can reach at most 12.5 %
of the HBM roof in useful bytes even if the DRAM interface is saturated.

**Common wrong answers.**

- Using 128-B cache lines instead of 32-B sectors for (c): that gives 32 × 128 B = 4,096 B and 3.1 %,
  which is the L1 line view, not what DRAM transfers on this architecture.
- Counting (b) as 4 sectors "because only 128 B are used".
- Forgetting that a misaligned base adds one sector in (a) (5 sectors, 80 %); state the alignment assumption.
