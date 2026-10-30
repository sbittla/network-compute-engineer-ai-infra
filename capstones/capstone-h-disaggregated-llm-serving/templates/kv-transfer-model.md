# KV-Cache Size and Transfer Model

> Template for Capstone H artifact 2. Show formula → values → result for every row. `[MODELED]`

## 1. Size
KV bytes/token = 2 × layers × KV heads × head dim × bytes = `<fill>` = `<fill>` B

| Prompt tokens | KV bytes | GB |
|---|---|---|
| 2,048 | `<fill>` | `<fill>` |
| 4,096 | | |
| 32,768 | | |

## 2. Transfer time
| Prompt | Link | Achievable GB/s | Raw transfer | Exposed (pipelined) | Exposed (not pipelined) |
|---|---|---|---|---|---|
| 2,048 | rdma-400g-x8 | `<fill>` | | | |
| 2,048 | tcp-200g-x2 | | | | |
| 32,768 | `<fill>` | | | | |

## 3. Aggregate demand
`<fill: rate × mean prompt × KV bytes; per prefill instance; the compute-bound ceiling on KV emission>`

## 4. Layout and lifecycle
`<fill: per-layer, per-TP-shard layout; when KV is freed on the prefill side; what happens if the decode side cannot accept it>`
