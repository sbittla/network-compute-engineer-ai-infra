# Cost Analysis

## 1. Inputs

| Input | Value | Label |
|---|---|---|
| Cost per GPU-hour (fully loaded) | <fill> | `[ILLUSTRATIVE]` |
| Fleet utilization | <fill> | `[ILLUSTRATIVE]` |
| GPUs per replica / replicas per node | <fill> | |

## 2. Cost per million tokens `[MODELED]` from `[SIMULATED]` throughput

| Config | Node load | Total (input + output) tokens/s per replica | **$/M total tokens (headline)** | $/M output tokens (all cost on output; upper bound) | SLO met? |
|---|---|---|---|---|---|
| <fill> | | | | | |

Explain why cost per token at the highest load is meaningless if the SLO is not met, and quote the
lowest **SLO-compliant** cost per configuration.

## 3. Input versus output pricing

<fill: allocate replica time between prefill and decode, or justify a ratio, and derive separate
input/output prices.>

## 4. Fleet cost for the forecast

<fill: nodes × 8 GPUs × $/GPU-hour × hours; cost per month; sensitivity to utilization and traffic mix
(the long-context tenant's share of cost).>

## 5. Levers

| Lever | Effect on cost | Risk |
|---|---|---|
| FP8 weights (c3) | <fill> | <fill: quality> |
| Isolating long-context traffic | <fill> | |
| Higher utilization via autoscaling | <fill> | |
