# Marking scheme: WP2 FP8 serving on half a node

Type worked-problem · kind computed · tier L1 · 15 points

**Evidence required:** All arithmetic shown; a before/after table; one sentence on what would have to be measured to trust (c).

| Criterion | Points |
|---|---|
| (a) weights 17.5 GB and KV 5.37 GB per GPU (KV still BF16, split over 4 GPUs), 22.87 GB total | 4 |
| (b) memory bound 6.83 ms and compute bound 0.566 ms at the FP8 peak of 1,979 TFLOP/s | 4 |
| (c) about 2,950 tokens/s per replica and about 5,900 per node with two replicas, about 1.75x BF16 TP 8 | 4 |
| (d) 64 FLOP/B against FP8 balance of about 591 FLOP/B, still memory-bound; one sentence on what to measure | 3 |
