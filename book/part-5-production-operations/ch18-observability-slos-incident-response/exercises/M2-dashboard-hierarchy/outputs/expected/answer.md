# M2 — Dashboard hierarchy from fleet to workload (model answer)

Figure 18.2 + Table 18.6; the lab's `dashboard_spec()` is the machine-checked skeleton (levels
fleet → node → device → workload, drill-downs chain, a burn-rate panel at fleet level, DCGM profiling
metrics).

| Level | Question | Panels (query sketch, unit) | Drill-down key |
|---|---|---|---|
| Fleet | Are users getting what was promised? | training throughput ratio per job (`job:train_throughput:ratio`, ratio); inference burn 1 h/5 m (`slo:errors:ratio_rate1h / 0.001`, ×) and TTFT p95 (`histogram_quantile(0.95, …)`, s); schedulable vs allocated GPUs (count); top-5 switches by PFC pause and ECN (`topk(5, switch:pfc_pause_tx:rate1m)`, frames/s); change and incident annotations | `job_id` / `service` |
| Node | Which nodes deviate from their job peers? | SM active and power per node grouped by job (`avg by (Hostname) (DCGM_FI_PROF_SM_ACTIVE)`, fraction; W); backend NIC TX/RX (B/s); PSI pressure (%); health/lifecycle state | `Hostname` → GPU UUID, `mlx5_N`, leaf port (LLDP) |
| Device: GPU | Which GPU and why? | SM clock and event-reason bitmask (MHz, bitmask); temperature (°C); ECC/Xid (count) | `job_id`, `rank` |
| Device: NIC | Is the host edge losing or pausing? | CNPs handled/sent, out-of-sequence, `rx/tx_prio3_pause` rate and duration (per s) | leaf port |
| Device: switch port | Where in the fabric? | ECN marks, PFC pause TX/RX, queue watermark, FEC/symbol errors, optic RX power (per s, bytes, dBm) | job via port → host mapping |
| Workload | What did the job experience? | step time p50/p95 (`train_step_seconds`, s); tokens/s; checkpoint duration (s); per-rank collective wait (log/flight-recorder query, s); TTFT/TPOT traces | back to fleet, same time range |

**Fleet mock-up (ASCII):**
```text
+--------------------------------- ORION fleet [time range] [annotations: CHG/INC] ---------------+
| Training throughput ratio per job        | Inference: burn 1h / 5m   | TTFT p95 / TPOT p95       |
|  trn-70b 0.82 ▼  ft-13b 0.85 ▼ (<0.909)  |  chat-70b 0.4 / 0.2       |  0.62 s / 38 ms           |
+------------------------------------------+---------------------------+---------------------------+
| Schedulable vs allocated GPUs  220/256   | Top-5 switches: PFC pause TX, ECN marks (per s)       |
+------------------------------------------+-------------------------------------------------------+
```

**Rules:** peer comparison beats absolute thresholds; the same time range passes through every link;
units on every axis (bits vs bytes explicit); ≈ 10 panels per level, not 40.

**Rejected panels:** (1) fleet-wide average `GPU_UTIL`: time-occupancy stays ≈ 97 % during network
stalls and is low on healthy idle inference nodes, so it misleads in both directions (K1); (2)
per-port counters for every switch port at fleet level: thousands of series, unreadable; the top-N
panel answers the fleet question and the per-port view belongs at device level.
