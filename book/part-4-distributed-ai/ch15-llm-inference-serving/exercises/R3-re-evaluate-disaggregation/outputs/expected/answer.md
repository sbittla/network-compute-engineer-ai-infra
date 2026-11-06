# R3 — When to re-evaluate disaggregation: worked solution

**Traffic change.** Growth in **prompt tokens per request**, or in the prompt:output ratio. The typical
trigger is RAG or document-QA adoption moving average prompts from 2k toward 8k tokens. The shared-pool
recommendation of Section 15.12 rests on a prefill share of ρ ≈ 0.45 at 2k prompts. Prefill time grows
linearly (and super-linearly with attention) in prompt length, while output length stays short.

**Leading metric.** **ρ_prefill**, the fraction of engine iterations (or GPU time) spent on prefill
chunks, per replica. It is computable from engine logs (prefill tokens per second × prefill time per
token). As it rises, mean TPOT inflates by 1/(1 − ρ) and **ITL p99** rises with it, *before* TTFT p95
breaches its SLO, because queueing delay stays small until ρ approaches 1.

**Thresholds I would set.**

- Warning: ρ_prefill > 0.55 sustained over a 1 h peak window, or ITL p99 > 2× its baseline (for example
  > 60 ms with chunked prefill at a 30 ms baseline).
- Re-evaluation trigger: the modeled shared-pool TPOT at the observed prompt mix comes within 20 % of the
  TPOT SLO, or mean prompt length ×2 from the design point.

At that point rerun the O4/D1 comparison with the observed prompt distribution. At 8k prompts the
model already favours disaggregation over RDMA (TPOT 16.7 vs 23.0 ms, worst ITL 32.5 vs 375 ms).
