# Marking scheme: K4 Prefill and decode

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** Definitions of prefill and decode and the bounding resource of each.

| Criterion | Points |
|---|---|
| Prefill defined (all prompt tokens processed in parallel, produces the KV cache and the first token) and called compute-bound | 2 |
| Decode defined (one token per sequence per step, re-reads all weights and the KV cache) and called HBM-bandwidth-bound | 1 |
| Supports the claim with intensity or an ORION number (decode about 32 FLOP/B at batch 32 against machine balance about 295 FLOP/B) | 1 |
