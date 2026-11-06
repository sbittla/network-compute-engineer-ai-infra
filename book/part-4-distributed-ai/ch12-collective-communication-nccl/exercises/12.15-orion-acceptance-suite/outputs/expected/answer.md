# 12.15 — ORION collective acceptance suite (model answer)

Baselines from Table 12.7 `[SIMULATED]` lab values; thresholds `[ILLUSTRATIVE]` policy.

| # | Test | Communicator shape | Sizes | Reps | Pass criterion (statistic) | When |
|---|---|---|---|---|---|---|
| 1 | `all_reduce_perf`, `all_gather_perf`, `reduce_scatter_perf` | 1 node, 8 GPUs | 8 B – 8 GiB, ×2 | 5 launches | Plateau (median busbw of 1–8 GiB) ≥ 95 % of fleet median: ≈ 450 GB/s with NVLS, ≈ 360–380 GB/s ring-only (state which); 8 B time ≤ 1.2 × fleet median; `#wrong` = 0 | Join + nightly |
| 2 | `all_reduce_perf` | Node under test + known-good reference node (16 ranks) | 8 B – 8 GiB | 5 | Plateau ≥ 95 % of 352 GB/s (c2); α ≤ 1.2 × 28 µs; CV of large-size busbw < 0.02 | Join + nightly |
| 3 | `all_reduce_perf` | Rail-pinned: one GPU per node, rail i only, 2–8 nodes | 1 MiB – 4 GiB | 3 | Each rail ≈ 45 GB/s busbw (≥ 95 % of that rail's fleet median); no rail > 5 % below its siblings | Join + nightly, per rail |
| 4 | `all_reduce_perf` | Full 8 nodes (64 ranks), rail-aligned | 8 B – 8 GiB | 5 | Plateau ≥ 95 % of 345 GB/s (c5); α ≤ 1.2 × 47 µs; CV < 0.02 | Weekly / after fabric changes |
| 5 | `alltoall_perf` | 8 nodes | 1 KiB – 1 GiB | 3 | busbw ≥ 90 % of fleet baseline; no PFC storm or discards outside policy on the leaves | Idle windows only |
| 6 | `sendrecv_perf` | Pairs on the same rail | 8 B – 1 GiB | 3 | ≥ 95 % of 45 GB/s; latency within 10 % of baseline | Join |

**Statistics.** Report median and minimum over launches, never the "Avg bus bandwidth" line; fail on
any `#wrong` ≠ 0 or any NCCL warning/error.

**Run-time budget.** ≤ 15 minutes per node for join tests (1, 2, 3, 6); ≈ 10 minutes for the weekly
8-node tests.

**Artifacts recorded.** Raw logs, `NCCL_DEBUG=INFO` start-up logs (channels, NIC bindings, `GDRDMA`),
`NCCL_TOPO_DUMP_FILE`, an environment manifest (driver, CUDA, NCCL, firmware, image digest, `NCCL_*`
variables, node list), switch and NIC counters before/after.

**Safety constraints.** Only drained or reserved nodes; never on rails shared with production jobs
during business hours; all-to-all only in declared idle windows because it stresses spine buffers for
everyone; abort on fabric alarms.

**Defence of one trade-off (coverage vs time vs fabric impact).** A node only needs to prove its own
GPUs, NVLink and eight NICs before joining, so the join suite uses single-node, pair and rail-pinned
tests: they localize a fault to a node and a rail in about 15 minutes and touch only one leaf port per
rail. Full 8-node and all-to-all runs add coverage of spines and incast behaviour, but they occupy 64
GPUs and load every spine; running them weekly in idle windows rather than per join keeps fabric impact
low while still catching fabric-wide regressions within days.
