# K4 — Prefill and decode

Source: manuscript Sections 1.2, 1.6 (arithmetic intensity) and 1.9 Steps 5–6. Numbers `[MODELED]`.

**Prefill** processes all prompt tokens of a request through every layer at once. The work is large
matrix multiplies (2,048 tokens × 8,192 hidden), so intensity is high and prefill is **compute-bound**:
a 2,048-token prompt on W-INFER needs 35.8 TFLOP per GPU, a 36.2 ms compute bound against a 20.9 ms
NVLink bound (Step 6). Prefill produces the KV cache and the first output token, so it sets TTFT.

**Decode** generates one token per sequence per step. Each step must read every weight (17.5 GB per GPU at
TP 8) plus the batch's KV cache (2.68 GB per GPU at batch 32 × 2,048 tokens) but performs only 2 FLOPs
per parameter per sequence. Intensity is ≈ *B* FLOP/B (32 at batch 32, ≈ 28 with the KV cache), about a
tenth of the 295 FLOP/B machine balance, so decode is **HBM-bandwidth-bound** (6.02 ms bound for a
9.5 ms observed step). It stays memory-bound at any batch size at this context length: as *B* grows,
the KV cache caps intensity at ≈ 209 FLOP/B, still below balance. Decode sets TPOT.

**Common wrong answer:** "decode is compute-bound because it runs a GPU at high utilization": utilization
counts any running kernel (K7).

**Marking note:** the key gives 2 points; this folder scores it out of 4.
