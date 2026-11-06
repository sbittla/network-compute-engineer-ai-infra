# Marking scheme: 6.4 MFU and HFU

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** formulas, recomputation argument, recommendation.

| Criterion | Points |
|---|---|
| Formulas: MFU = 6N × tokens/s / (GPUs × peak); HFU counts executed FLOPs including recomputation (about 8N per token with full recomputation) | 1 |
| HFU exceeds MFU because recomputed forward passes are work the model does not require | 1 |
| Report MFU (with convention and the vendor dense peak) when comparing clusters | 1 |
