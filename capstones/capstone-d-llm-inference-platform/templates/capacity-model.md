# Capacity Model

## 1. Per-replica memory plan `[MODELED]`

Show the arithmetic for each configuration (formula → substitution → result).

| Quantity | c1 (BF16, TP8) | c3 (FP8, TP4) |
|---|---|---|
| Weights | <fill> | <fill> |
| Usable HBM (tp × 80 GB × utilization) | <fill> | <fill> |
| Runtime reserve | <fill> | <fill> |
| KV budget | <fill> | <fill> |
| KV bytes per token | <fill: 327,680 B; explain the KiB/KB trap in the vendor sheet> | |
| KV tokens; sequences at 4k context | <fill> | <fill> |

## 2. Iteration cost `[MODELED]`

| Case | Compute time | Memory time | Bound | Iteration time |
|---|---|---|---|---|
| Prefill chunk of 2,048 tokens, TP8 BF16 (linear 2·N·n + causal attention 2·L·d·((p+c)² − p²)) | <fill> | <fill> | <fill> | <fill> |
| Full 32k prompt: attention share of prefill FLOPs | <fill: ≈ 30 % on top of 2·N·n> | | | |
| Decode, 64 sequences × 2k context, TP8 BF16 | <fill> | <fill> | <fill> | <fill> |
| <fill: same for TP4 FP8> | | | | |

What chunk size keeps every mixed iteration (i.e. each inter-token gap) under 50 ms? <fill: show the algebra; relate it to ITL p99, not mean TPOT>

## 3. Load sweep `[SIMULATED]`

| Config | Node load × | Mix | Stable (all seeds) | TTFT p95 median [min–max] | TPOT p95 | ITL p99 | Goodput | SLO met (all seeds) |
|---|---|---|---|---|---|---|---|---|
| <fill> | | | | | | |

Chart: <fill: TTFT p95 and TPOT p95 versus node load per configuration, with SLO lines; caption>

Highest node load meeting the SLO per configuration: <fill>

## 4. Fleet size for the forecast

| Item | Value |
|---|---|
| Forecast peak (node-load units, 1.0 = trace rate) | <fill> |
| Max SLO-compliant load per node (chosen config, chosen mix routing) | <fill> |
| Headroom policy (N+k, failure of one replica, deploy surge) | <fill> |
| Nodes required | <fill: show the rounding> |

## 5. Bottleneck analysis

<fill: which resource limits each configuration at its knee (prefill compute, HBM bandwidth, KV
capacity, scheduler policy), with the evidence from your sweep.>
