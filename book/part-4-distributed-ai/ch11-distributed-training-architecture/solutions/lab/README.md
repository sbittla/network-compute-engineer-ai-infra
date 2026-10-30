# Lab 11 — Instructor Notes (reference solution and planted traps)

Reference implementation: `stepmodel.py` (passes `python ../../lab/check.py --impl solution`).
Run `python stepmodel.py` to print the full candidate table and checkpoint table.

## Expected results `[MODELED]`

| Candidate | Mem (GB) | Step (s) | MFU | Verdict |
|---|---|---|---|---|
| D_tp4_pp8_dp8 | 38.8 | 16.07 | 43.3 % | **Recommended** |
| A_baseline_tp8_pp4_dp8 | 27.4 | 17.45 | 39.9 % | Feasible (≈ REFERENCE_CLUSTER 17.4 s / 40 %) |
| B_tp8_pp2_dp16 | 36.2 | 17.45 | 39.9 % | Feasible |
| H_tp8_pp1_dp32 | 53.7 | 17.46 | 39.8 % | Feasible |
| C_tp8_pp8_dp4 | 23.1 | 17.47 | 39.8 % | Feasible |
| L_tp8_pp4_dp8_mb2 | 38.8 | 17.66 | 39.4 % | Feasible |
| F_fsdp_tp1_pp1_dp256 | 17.2 | 18.55 | 37.5 % | Feasible, slow (full recompute; 9.4 s of DP traffic must be fully prefetched) |
| K_tp8_pp4_dp8_fullrecomp | 16.7 | 22.17 | 31.4 % | Feasible, slow (recompute) |

DP exposure uses the overlap window (last micro-batch's backward = compute/m × 2/3 ≈ 72 ms for the
baseline): exposed DP = max(0, T_DP − window) ≈ 98 ms.

## Planted traps (why they are there)

| Trap | What the learner must notice | Teaching point |
|---|---|---|
| `J_tp2_pp8_dp16` — 70.4 GB | Fastest row on paper; fits 80 GB but exceeds the 68 GB headroom policy | "Fits" is not the acceptance criterion; fragmentation and longer sequences need headroom |
| `I_tp8_pp4_dp8_mb4_zero0` — 84.6 GB | Same parallelism as baseline; overflow comes from micro-batch 4 (4× activations) plus unsharded optimizer state (35 GB) | Innocent-looking knob changes cause OOM at scale |
| `G_tp1_pp4_dp64` — 168.5 GB | Looks attractive (no TP traffic; 16.6 s) but needs 2× an H100's memory | Always check memory before speed |
| `E_tp16_pp2_dp8` | TP group spans two nodes (TP time 4.1 → 13.1 s) **and** 8 KV heads not divisible by 16 | TP must stay in the NVLink domain; GQA constrains TP |
| `F_fsdp_tp1_pp1_dp256` | Fits easily, but DP traffic is 1.5 × m all-reduce-equivalents of 140 GB (9.4 s) that must hide entirely behind compute | ZeRO-3 + accumulation on a 50 GB/s/GPU fabric is fragile |
| Shuffled `candidates.csv` (seed 11) | Row order carries no information | Sort by the metric you are optimizing |

## Grading notes

- Accept a learner recommendation other than D only if they changed an assumption in
  `cluster_orion.yaml` *and* say so (e.g., kernel efficiency depending on TP degree). The checker uses
  the shipped assumptions.
- The most common bug is forgetting `min(pp, m)` in-flight micro-batches (activations 4× too small
  for PP = 4) — which makes J and I look safe.
- Second most common: counting TP collectives per stage *without* multiplying by micro-batches.
