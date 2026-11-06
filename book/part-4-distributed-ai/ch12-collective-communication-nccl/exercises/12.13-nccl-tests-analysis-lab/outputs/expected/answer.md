# 12.13 — nccl-tests analysis toolkit (instructor solution)

**Reference run.** `python lab/check.py --impl solution` → `11/11 checks passed`; the captured report
is `solutions/lab/outputs/check_solution.txt`, and the checks this exercise depends on are listed in
`outputs/lab_checks.json`. Data `[SIMULATED]`; fits `[MODELED]`.

**Key checker values.** `bus_factor`: all_reduce(8) = 1.75, all_gather(8) = 0.875, reduce_scatter(16) =
0.9375, broadcast = 1. `parse_nccl_log`: 31 rows, 16 ranks, 2 nodes, 20 iterations (c2).
`plateau_busbw`: 449.1 GB/s (1 node), 345.2 GB/s (8 nodes). `fit_alpha_beta` (c2): α = 28.1 µs,
B = 354.3 GB/s, n½ = 5.31 MB. `jitter_cv`: c5 0.016, c6 0.088. `predict_time_us`: 1 GiB on 16 ranks →
5,699 µs. `analyze_all`: c5 plateau 345 GB/s vs the reported "Avg bus bandwidth" of 117 GB/s.

**Summary table.** As in Exercise 12.11 (α, B, n½, plateau, regions for c1–c6).

**Anomaly labels and explanations.**

| Config | Label | Explanation |
|---|---|---|
| c1 | ok | Single node: its own class (NVLS, 449 GB/s); not compared with multi-node rows |
| c2, c4, c5 | ok | Plateau 345–352 GB/s, CV ≈ 0.02: the aligned baseline |
| c3 | `low_plateau_steady` | 184 GB/s (< 75 % of the 346 GB/s multi-node median), low jitter: a mapping/topology problem — half the NICs in use (Exercise 12.12) |
| c6 | `low_plateau_jittery` | 177 GB/s and CV 0.088: a degraded link or rail; the node list changed (orion-n12 replaced orion-n08), so suspect n12's NICs/cables (Chapter 10) |

**Why "Avg bus bandwidth" misleads.** It averages busbw over all sizes, including tiny latency-bound
rows near 0 GB/s, so c5 reports 117 GB/s although its plateau is 345 GB/s (Exercise 12.16).

**Optional gloo run.** If submitted, it must carry `[MEASURED]`, the PyTorch and gloo versions, CPU,
thread count and whether loopback or a real NIC was used; the parser should read it if the column
layout matches.
