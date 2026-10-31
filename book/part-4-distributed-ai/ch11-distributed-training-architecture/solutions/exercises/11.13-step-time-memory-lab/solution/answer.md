# 11.13 — Step-time and memory model (instructor solution)

**Reference run.** `python lab/check.py --impl solution` → `10/10 checks passed`; the captured report
is `solutions/lab/outputs/check_solution.txt` and the checks this exercise relies on are listed in
`outputs/lab_checks.json`. All numbers `[MODELED]` from Table 11.4's `[ILLUSTRATIVE]` assumptions.

**Candidate table** (sorted by step time; memory for pipeline stage 0):

| Candidate | Mem (GB) | Step (s) | MFU | Verdict |
|---|---|---|---|---|
| J_tp2_pp8_dp16 | 70.4 | 15.94 | 43.7 % | exceeds 68 GB headroom (fits 80 GB) |
| **D_tp4_pp8_dp8** | **38.8** | **16.07** | **43.3 %** | **feasible — recommended** |
| G_tp1_pp4_dp64 | 168.5 | 16.55 | 42.0 % | HBM overflow |
| B_tp8_pp2_dp16 | 36.2 | 17.45 | 39.9 % | feasible |
| A_baseline_tp8_pp4_dp8 | 27.4 | 17.45 | 39.9 % | feasible |
| H_tp8_pp1_dp32 | 53.7 | 17.46 | 39.8 % | feasible |
| C_tp8_pp8_dp4 | 23.1 | 17.47 | 39.8 % | feasible |
| L_tp8_pp4_dp8_mb2 | 38.8 | 17.66 | 39.4 % | feasible |
| I_tp8_pp4_dp8_mb4_zero0 | 84.6 | 18.27 | 38.1 % | HBM overflow |
| F_fsdp_tp1_pp1_dp256 | 17.2 | 18.55 | 37.5 % | feasible |
| K_tp8_pp4_dp8_fullrecomp | 16.7 | 22.17 | 31.4 % | feasible but slow |
| E_tp16_pp2_dp8 | 21.7 | 23.94 | 29.1 % | invalid: TP spans nodes, KV heads not divisible |

8 feasible candidates.

**Recommendation.** `D_tp4_pp8_dp8`: 16.07 s, 43.3 % MFU, 38.8 GB — 8 % faster than the baseline
because TP = 4 cuts per-GPU TP bytes by 7/3 (the (t − 1) identity of 11.9) and exposed TP from 3.08 to
1.33 s, while the larger bubble (5.2 % vs 2.3 %) costs less than it saves; 29 GB of headroom remains.
Risk to state: TP = 4 puts two DP replicas' TP groups on one node, so DP peers are no longer all
rail-aligned — validate with rank-map checks (Chapter 12).

**Checkpoint table.** As in 11.12: ORION-256 sync τ_opt 65.7 min, waste 2.80 %; XL sync 16.4 min,
17.5 %; a 4-hour interval at XL is invalid (completes with p = 0.26).

**Planted traps.** J is the fastest but violates the 85 % headroom policy (70.4 GB); G (ZeRO-1 with
TP = 1) and I (ZeRO-0, micro-batch 4) overflow 80 GB; E (TP = 16) spans two NVLink domains and 8 KV
heads cannot split over 16 ranks; K (full recompute) fits easily but costs 27 % step time; F
(FSDP over 256 GPUs) moves 9.4 s of DP traffic per step and survives only because ZeRO-3 overlaps it
with the whole compute.
