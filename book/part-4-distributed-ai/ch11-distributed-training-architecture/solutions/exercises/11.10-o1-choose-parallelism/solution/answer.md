# 11.10 (O1) — Choose a parallelism for three constraints

Method: Sections 11.2–11.8; assumptions Table 11.4 (68 GB planning limit, 4 GB overhead). Values
`[MODELED]`. Accept other layouts with a correct memory proof and traffic accounting. Each case: layout
→ memory → dominant traffic → links.

**(a) 1.3B model, s = 2,048, global batch 512, 64 GPUs → pure DP (DDP or ZeRO-1), DP = 64.**

- Memory: model state 16 B × 1.3e9 = 20.8 GB per GPU (no sharding needed). Assume h ≈ 2,048 and 24
  layers: activations per sequence ≈ 2,048 × 2,048 × 34 × 24 = 3.4 GB. 512/64 = 8 sequences per GPU per
  step as b = 4 with 2 accumulation steps → 13.7 GB. Total ≈ 20.8 + 13.7 + 4 = **38.5 GB** < 68 GB.
- Traffic: one gradient all-reduce of 2 B × 1.3e9 = 2.6 GB per step; each GPU sends 2 × 63/64 × 2.6 ≈
  5.1 GB, bucketed and overlapped with backward. Hierarchical time 2(7/8) × 2.6/300 + 2(7/8) × (2.6/8)/45 ≈
  0.015 + 0.013 = **0.028 s** against ≈ 0.26 s of compute (6 × 1.3e9 × 1,048,576 / 64 / 4.945e14).
- Links: NVLink inside each node (reduce-scatter/all-gather), then all 8 rails between the 8 nodes, each
  GPU on its own rail. TP or PP would add critical-path traffic for no memory benefit.

**(b) W-TRAIN at s = 4,096 on 64 GPUs, global batch 256 → TP 8, PP 4, DP 2, ZeRO-1** (alternatives
TP 8/PP 8/DP 1 or TP 4/PP 8/DP 2).

- Memory: P = 70e9/32 = 2.1875e9; states (2 + 2 + 12/2) × P = 21.9 GB; m = 256/2 = 128; activations
  142.6 MB × 20 layers × 4 in flight = 11.4 GB; total **37.3 GB**.
- Traffic: TP 1.2 TB per GPU per step (same per-GPU work as the 256-GPU baseline; compute 13.9 s);
  DP 2 × 1/2 × 4.375 GB = 4.4 GB (≈ 0.10 s); PP 2 × 128 × 8.4 MB = 2.15 GB.
- Links: TP on NVLink; DP and PP on the GPU's own rail (TP = 8 keeps every peer rail-aligned, 11.5).
- TP 4/PP 8/DP 2 variant: 21.9 + 22.8 + 4 = 48.7 GB, TP bytes 515 GB (fewer, but TP 4 leaves DP peers
  on the same node).

**(c) 70B fine-tune, s = 65,536, global batch 32, 32 GPUs → TP 8, PP 4, DP 1 with full recompute**
(alternative TP 8 + CP 2–4 with the optimizer sharded over CP).

- Selective recompute is impossible: 65,536 × 8,192 × 34/8 = 2.28 GB per layer per sequence × 20 × 4 =
  **182 GB**. Full recompute stores only the layer input, 65,536 × 8,192 × 2/8 = 134 MB per layer → 10.7 GB.
  States 2.1875e9 × 16 B = 35 GB (DP = 1: nothing to shard over). Total ≈ **49.7 GB**.
- Traffic: M = 65,536 × 8,192 × 2 = 1.07 GB per TP collective; 4 × 1.75 × 1.07 GB × 20 × 32 = 4.8 TB per
  GPU per step, ≈ 7.2 TB including the recomputed forward's collectives (×1.5) — ≈ 24 s at 300 GB/s, on
  NVLink. PP: 2 × 32 × 134 MB = 8.6 GB over the rail. Bubble 3/35 = 8.6 %.
- Note: attention FLOPs (≈ 12·L·h·s per token) are comparable to 6N at this length and are not in 6ND,
  so compute estimates are optimistic.

**Common wrong answers.** Using TP for the 1.3B model; ignoring the in-flight factor in (b); proposing
selective recompute in (c); putting TP across nodes.
