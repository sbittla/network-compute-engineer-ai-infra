# Marking scheme: 13.13 One slow node in a TP job

Type troubleshooting · kind written · tier L1 · 12 points

**Evidence required:** ≥ 3 ranked hypotheses, tests, root cause, fix, validation

| Criterion | Points |
|---|---|
| At least three ranked hypotheses, with degraded NVLink on n09 ranked first, the container IPC/P2P (SHM fallback) hypothesis considered, clocks/network rejected with stated evidence, and Fabric Manager rejected because the job would not have started | 3 |
| Discriminating tests with real commands and expected output (nvlink --status, topo -m NV6 vs NV18, nvlink -e / DCGM NVLink error fields, single-node all_reduce_perf, NCCL INFO P2P/CUMEM vs SHM) | 3 |
| Root cause: degraded NVLink on one n09 GPU after the reboot (fewer links trained), giving about 3x TP time | 2 |
| Safe fix: checkpoint, drain, restart at reduced DP or wait for repair; repair and acceptance under change control | 2 |
| Validation with numbers: 18 links active (NV18), error counters flat, single-node busbw within 5 % of fleet median, job TP time within 5 % | 2 |
