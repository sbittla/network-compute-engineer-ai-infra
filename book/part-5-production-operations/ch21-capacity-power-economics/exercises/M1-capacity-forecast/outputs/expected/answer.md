# M1 — Capacity forecast: worked solution

Sources: manuscript Sections 21.2, 21.3 (Table 21.2 lead times) and 21.9 (Table 21.9); lab Tasks 1–2;
`lab/data/quarterly_plan.csv` and `assumptions.yaml` `[ILLUSTRATIVE]`. Results `[MODELED]`;
`solve.py` writes the full quarterly tables `forecast_p50.csv` and `forecast_p90.csv`.

**Method.** (1) Drop the exact duplicate 2027Q3 row (12 quarters remain). (2) Installed = 256 +
deliveries − retirements. (3) Energizable = ⌊facility kW / 1.428 / 8⌋ × 8 (420 / 800 / 1,500 kW →
288 / 560 / 1,048 GPUs). Energized = min(installed, energizable). (4) Usable = energized × 0.8496.
(5) Required = demand / 0.85, with p90 demand = 1.25 × p50 from 2028Q3. (6) Binding resource: compare
the energized GPUs needed (required / 0.8496) with installed and energizable.

**Shortfalls**

| Scenario | Quarter | Usable | Required | Gap | Binding | Order-by |
|---|---|---|---|---|---|---|
| p50 | **2028Q3** | 475.8 | 494.1 | −18.3 | power (1,024 installed, 560 energized) | facility power **2027Q3** |
| p50 | 2029Q4 | 870.0 | 964.7 | −94.7 | GPUs + power (needs 1,136 > 1,048) | GPUs 2029Q2, network 2029Q3, power 2028Q4 |
| p90 | **2028Q3** | 475.8 | 617.6 | −141.9 | power | facility power **2027Q3** |
| p90 | 2029Q2 | 890.4 | 926.5 | −36.1 | power (1,280 installed, 1,048 energized; 1,096 needed) | power 2028Q2 |
| p90 | 2029Q3 | 870.0 | 1,058.8 | −188.8 | GPUs + power (needs 1,248) | GPUs 2029Q1, network 2029Q2, power 2028Q3 |
| p90 | 2029Q4 | 870.0 | 1,205.9 | −335.9 | GPUs + power (needs 1,424) | GPUs 2029Q2, network 2029Q3, power 2028Q4 |

Both scenarios first fall short in **2028Q3**. The generic order-by for that quarter is GPUs 2028Q1,
network 2028Q2 and facility power 2027Q3, but only power fixes it.

**Where the scenarios diverge.** p50 has two isolated shortfalls. p90 is short in 4 of the last 6
quarters, and the 2028Q3 gap is 7.7× larger (−141.9 vs −18.3). Closing p90's 2028Q3 gap needs 728
energized GPUs, so the full phase 2 must be energized by then, not just one quarter earlier. The
in-quarter 550 W cap mitigation of Section 21.9 (≈ 501 effective usable) covers p50 but not p90's
617.6.

**Recommendation (decision rule from Section 21.3).** Commit facility power for p90: energize phase
2 (1,500 kW) by 2028Q3 (order by 2027Q3), and plan the hall's growth to ≈ 1.57 MW by 2029Q2 (1,096
GPUs × 1.428 kW, order by 2028Q2) and ≈ 2.03 MW by 2029Q4 (1,424 GPUs, order by 2028Q4). p50 alone
needs ≈ 1.62 MW by 2029Q4.
Order GPUs for p50 (+112 GPUs for 2029Q4, by 2029Q2). Hold a burst option (cloud or partner) for the
p90 − p50 difference of ≈ 240 GPUs in 2029Q4.

**Common wrong answers:** counting the duplicate row; applying the uplift before 2028Q3; calling
2029Q2 a GPU shortfall (232 GPUs are stranded there); ordering GPUs for a power shortfall.

*Key correction:* the key's p90 required values for 2029Q2 and 2029Q4 were 925.9 and 1,204.7.
787.5 / 0.85 = 926.5 and 1,025 / 0.85 = 1,205.9. The key also said 2029Q2 needs GPUs; it is power-bound.
