# Marking scheme: R4 Evidence for FP8 KV safety

Type reflection · kind written · tier L1 · 3 points

**Evidence required:** at least three distinct pieces of evidence (offline evaluation at real context length, canary signal, engine support), each with its acceptance criterion.

| Criterion | Points |
|---|---|
| Offline evaluation at the tenant's real context length (8-12k), BF16 vs FP8 KV on task metrics, with a criterion | 1 |
| Canary with per-tenant quality signals and a criterion | 1 |
| Engine support for the model's KV scaling method confirmed, with criterion; memory saving is not evidence of safety | 1 |
