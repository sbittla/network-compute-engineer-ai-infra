# M1 — SLI/SLO specification for ORION (model answer)

Window 30 days = 43,200 min. Targets `[ILLUSTRATIVE]`, arithmetic `[MODELED]`.

| Service | SLI (good / valid) | Source | SLO | Budget (30 d) | Burn policy | Owner |
|---|---|---|---|---|---|---|
| Training job recovery (completion) | Infrastructure-attributed interruptions after which the job resumed (first step) within 30 min / all infrastructure-attributed interruptions | scheduler + step records + incident attribution | 95 % | 5 % of interruptions: a 256-GPU job sees ≈ 720 / 48 = 15 per month → 0.75 slow recoveries | ticket per miss; page if 2 in 24 h | training-infra |
| Training throughput | Job-minutes with median step ≤ 1.10 × baseline / running job-minutes after warm-up | app histogram + baseline gauge | 99 % | 0.01 × 43,200 = 432 slow minutes per job-month | 1 h/5 m > 14.4 page | training-infra |
| Inference latency | Requests with TTFT ≤ 800 ms (2k prompt class) / successful requests; tokens with TPOT ≤ 50 ms / output tokens | serving histograms | 95 % each | 5 %: at 3,000 req/min → 6.48 M slow requests | 1 h/5 m > 14.4 (max burn 20) | inference |
| Inference availability | Non-5xx / valid requests (client 4xx excluded) | gateway | 99.9 % | 43.2 min of full outage | Table 18.5 | inference |
| Cluster availability | Minutes with ≥ 24 of 32 nodes healthy *and* schedulable, outside announced maintenance / all such minutes | kube-state-metrics, `sinfo`, health checks | 99.5 % | 0.005 × 43,200 = 216 min | 6 h/30 m > 6 page; 3 d ticket | fleet |
| Fabric health | Probe runs ≥ 90 % of commissioning busbw / probe runs; 5-min backend link-windows with zero FEC-uncorrectable or link-down / all link-windows | probe job + gNMI | 99 % / 99.9 % | hourly probe per rail: 8 × 720 = 5,760 probes → 57.6 failures; 256 host links × 8,640 windows = 2,211,840 → 2,212 bad windows | ticket on 3 d; page only via training symptom | fabric |

**Targets derived from the canon, not chosen:**
- *Completion:* node MTBF 1,536 h → a 16-node job's MTBF is 96 h; P(no interruption in 24 h) =
  e^(−24/96) = **0.78** (32 nodes: e^(−0.5) = 0.61). "95 % of 24 h attempts uninterrupted" would be
  violated by design, so the SLI measures recovery, which the platform controls.
- *Availability:* 5-day repair turnaround → mean 2.5 nodes in repair (Poisson). "≥ 31 nodes" holds
  P(≤ 1) = 0.29; allowing 7 down, P(≤ 7) = 0.9958, so repair alone would use ≈ 85 % of the 0.5 %
  budget; allowing 8 down (≥ 24 of 32), P(≤ 8) = **0.9989**, leaving most of the budget for real
  outages.

**Recording rules (one per SLI, `[ILLUSTRATIVE]` metric names):**
```yaml
- record: job:train_throughput:ratio
  expr: job:train_step_baseline_seconds / job:train_step_seconds:median10m
- record: job:train_slow_minutes:ratio_rate1h
  expr: avg_over_time((job:train_throughput:ratio < bool 0.909)[1h:1m])
- record: slo:ttft_good:ratio_rate5m
  expr: sum(rate(vllm:time_to_first_token_seconds_bucket{le="0.8"}[5m])) / sum(rate(vllm:time_to_first_token_seconds_count[5m]))
- record: slo:errors:ratio_rate5m
  expr: sum(rate(gateway_requests_total{code=~"5.."}[5m])) / sum(rate(gateway_requests_total{code!~"4.."}[5m]))
- record: cluster:healthy_schedulable_nodes:count
  expr: count(orion_node_lifecycle_state{state="schedulable"} == 1 and on(node) orion_node_healthy == 1)
- record: fabric:probe_good:ratio_1d
  expr: sum_over_time(fabric_probe_busbw_ok[1d]) / count_over_time(fabric_probe_busbw_ok[1d])
- record: job:recovered_within_30m:ratio_30d
  expr: sum(increase(orion_infra_interruptions_recovered_30m_total[30d])) / sum(increase(orion_infra_interruptions_total[30d]))
```

**Exclusions:** client 4xx; user-code failures and preemptions (attribution rule: an interruption
counts only when attributed to infrastructure); announced maintenance windows; warm-up minutes and
checkpoint steps. No component metric (e.g. "GPU util > 90 %") is an SLI.

`solve.py` computes every budget and derived probability.
