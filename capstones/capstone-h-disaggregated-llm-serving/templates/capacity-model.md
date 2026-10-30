# Capacity Model

> Template for Capstone H artifact 5. `[MODELED]` unless stated.

| Quantity | Formula | Value |
|---|---|---|
| Mean prefill time per request | mean of prefill_time_s over the trace | `<fill>` |
| Prefill instances P | ceil(rate × mean / ρ_max) | `<fill>` |
| Decode batch B | largest B with step ≤ 0.8 × TPOT SLO and KV fits | `<fill>` |
| Decode throughput per instance | B / step(B) | `<fill>` |
| Decode instances D | ceil(rate × mean output / (ρ_max × throughput)) | `<fill>` |
| KV GB/s total and per prefill instance | | `<fill>` |

## Utilisation at the target load for the deployed candidate
| Resource | Utilisation | |
|---|---|---|
| Prefill | `<fill>` | |
| Decode | `<fill>` | |
| Network egress per prefill instance (RDMA / TCP) | `<fill>` | |
| Network fan-in per decode instance (RDMA / TCP) | `<fill>` | |
| **Bottleneck** | `<fill>` | |

Model vs simulation: `<fill: steady-state prefill utilisation, model vs simulator, and why they differ>`
