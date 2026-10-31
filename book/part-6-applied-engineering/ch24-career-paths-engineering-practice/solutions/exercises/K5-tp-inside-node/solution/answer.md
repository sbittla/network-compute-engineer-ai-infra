# K5 — TP inside the node: worked solution

**Method** (manuscript Section 24.6, "Memory → parallelism"; inputs from Table 24.9). All results are
`[MODELED]`; the achieved bandwidths are `[ILLUSTRATIVE]` planning values.

1. **Payload of one TP all-reduce.** With one 4,096-token sequence per micro-batch and hidden size 8,192
   in BF16: 4,096 × 8,192 × 2 B = 67,108,864 B ≈ **67.1 MB**.
2. **Bytes each GPU sends in a ring over n = 8 GPUs:** 2 × (n − 1)/n × 67.1 MB = 2 × 7/8 × 67.1 MB ≈
   **117 MB**.
3. **Count per step.** Four TP all-reduces per layer (two forward, two backward), 80 / PP = 80 / 4 = 20
   layers per pipeline stage, and 1,024 / DP = 1,024 / 8 = 128 micro-batches per replica per step:
   117 MB × 4 × 20 × 128 ≈ **1.20 TB per GPU per step** `[MODELED]`.
4. **Time over NVLink** at the achieved 360 GB/s per direction (80 % of 450 GB/s line rate):
   1.20 TB / 360 GB/s ≈ **3.3 s**, on the critical path but affordable inside a 17.4 s step.
5. **Time over a NIC** at the achieved 40 GB/s (80 % of the 50 GB/s of a 400 Gb/s port):
   1.20 TB / 40 GB/s ≈ **30 s**, longer than the entire 17.4 s modeled step (and the 20 s target).

**Conclusion.** Moving TP off NVLink would multiply its cost by 360 / 40 = 9×, from about 19 % of the step
to more than the whole step. That one calculation is the argument for TP = 8 inside the NVLink domain,
which is also ORION's baseline (TP = 8, PP = 4, DP = 8) in `docs/REFERENCE_CLUSTER.md`.

**Common wrong answers.**
- Using the line rates (450 GB/s, 50 GB/s) without saying so: gives 2.7 s and 24 s. Not wrong in
  direction, but the assumption must be stated.
- Forgetting the 128 micro-batches (gives ≈ 9.4 GB and milliseconds, which hides the problem).
- Using 2× instead of 2(n − 1)/n for the ring (overstates by 8/7).
- Counting 80 layers instead of the 20 a stage holds.

`solve.py` recomputes every step and asserts 67.1 MB, 117 MB, 1.20 TB, 3.3 s and 30 s.
