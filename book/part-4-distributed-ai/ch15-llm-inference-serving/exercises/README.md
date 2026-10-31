# Chapter exercises — index

Each exercise has its own folder with the prompt and an `outputs/` folder for your work.

| ID | Title | Type | ★ | Tier | Kind | Folder |
|---|---|---|---|---|---|---|
| K1 | Why decode is memory-bound | knowledge-check | ★ | L1 | computed | [K1](K1-decode-memory-bound/) |
| K2 | Latency metrics | knowledge-check | ★ | L1 | written | [K2](K2-latency-metrics/) |
| K3 | Paged KV cache | knowledge-check | ★ | L1 | written | [K3](K3-paged-kv-cache/) |
| K4 | Static, dynamic and continuous batching | knowledge-check | ★ | L1 | written | [K4](K4-batching-strategies/) |
| K5 | Goodput | knowledge-check | ★ | L1 | written | [K5](K5-goodput/) |
| K6 | GQA and KV bytes per token | knowledge-check | ★ | L1 | computed | [K6](K6-gqa-kv-bytes/) |
| K7 | GPU utilization does not show saturation | knowledge-check | ★★ | L1 | written | [K7](K7-gpu-utilization-decode/) |
| K8 | Recompute versus swap | knowledge-check | ★★ | L1 | computed | [K8](K8-recompute-vs-swap/) |
| W1 | Capacity of an alternative layout | worked-problem | ★★ | L1 | computed | [W1](W1-long-context-tier-capacity/) |
| W2 | Sizing a shared pool with Little's law | worked-problem | ★★ | L1 | computed | [W2](W2-shared-pool-littles-law/) |
| L1 | Lab 15: capacity model, serving-trace analyzer, disaggregation model | hands-on-lab | ★★ | L1 | lab | [L1](L1-serving-lab/) |
| T1 | Token-2 stall in the disaggregated pool | troubleshooting | ★★★ | L1 | written | [T1](T1-token-2-stall/) |
| D1 | RAG serving tier | design-challenge | ★★★ | L1 | computed | [D1](D1-rag-serving-tier/) |
| O1 | Memory demand vs batch, sequence length and concurrency | outline-mandated | ★★ | L1 | computed | [O1](O1-memory-demand-table/) |
| O2 | Analyze a serving trace | outline-mandated | ★★ | L1 | computed | [O2](O2-analyze-serving-trace/) |
| O3 | Compare two serving configurations | outline-mandated | ★★ | L1 | computed | [O3](O3-compare-serving-configs/) |
| O4 | Prompt workload split across prefill and decode pools | outline-mandated | ★★★ | L1 | computed | [O4](O4-prompt-split-8k/) |
| O5 | Speculative decoding trade-off | outline-mandated | ★★ | L1 | computed | [O5](O5-speculative-decoding/) |
| R1 | Capacity-model assumptions to measure | reflection | ★ | L1 | written | [R1](R1-capacity-model-assumptions/) |
| R2 | What a 5 % ITL sample can show | reflection | ★★ | L1 | written | [R2](R2-sampled-itl-p999/) |
| R3 | When to re-evaluate disaggregation | reflection | ★★ | L1 | written | [R3](R3-re-evaluate-disaggregation/) |
| R4 | Evidence for FP8 KV safety | reflection | ★★ | L1 | written | [R4](R4-fp8-kv-safety/) |
| DEL | Inference capacity model and tuning recommendation | deliverable | ★★★ | L1 (L2 optional) | lab | [DEL](DEL-capacity-model-memo/) |

Exercise count: 23
