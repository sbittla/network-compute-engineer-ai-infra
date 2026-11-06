# Marking scheme: 17-K2 nodeSelector versus toleration

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** One sentence on attract vs repel; a correct YAML fragment.

| Criterion | Points |
|---|---|
| Selector/affinity attracts; taint repels and a toleration only permits | 1 |
| nodeSelector halcyon.ai/dedicated: search present | 1 |
| Toleration with key, operator Equal, value search, effect NoSchedule (toleration alone = half credit overall) | 2 |
