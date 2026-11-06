# Marking scheme: 17-K3 The three taint effects

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** Three effects with correct semantics.

| Criterion | Points |
|---|---|
| NoSchedule: blocks new non-tolerating pods, running pods stay | 1 |
| PreferNoSchedule: soft avoidance, never blocks | 1 |
| NoExecute: blocks new and evicts running non-tolerating pods (after tolerationSeconds) | 1 |
