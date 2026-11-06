# L1 — Attribute a cross-layer regression (solution)

Reference: `solutions/lab/regression_lab.py`; all values `[SIMULATED]` from the committed bundle (seed
2214). Rubric weights from lab README section 7.

**Checker.** In the instructor copy `python lab/check.py --impl solution` prints 12 PASS lines: the
data-regeneration check plus 11 task checks (tasks 1–9 plus 6b, the bootstrap, and the failed-job
population rule as a separate task-3 check), then `12/12 checks passed (solution); 0 skipped`. In the learner copy the
generator is absent, so the first check is `SKIP` and the line reads `11/11 checks passed (solution); 1 skipped`.
The `render_report` check also requires the `Hygiene:` line with the counts below.

**Data-hygiene note (the expected content).**

| Rule | Why | Effect on the bundle |
|---|---|---|
| Primary key `(job_id, step)`, keep first | Log-shipper replay of job 41105's stall steps | 44 duplicate rows removed (22 stall steps replayed twice more) |
| Exclude warm-up steps 0–9 | Init and compilation add up to +30 s; short jobs look worse | 480 rows removed (48 jobs × 10 steps) |
| Population = every job launched | Survivorship bias (Section 22.8) | 0 jobs removed; failed TP-split job 41114 kept with 60 usable steps |
| Time-aware joins (driver, alert) | Inventory shows *current* driver; before-period jobs ran R550 | `driver_new` = 12 after-period jobs, not 24; `alert_node` = 6 jobs after the alert start |

Rows: 9,514 raw − 44 − 480 = **8,990**.

**Expected results.**

| Quantity | Value |
|---|---|
| TP-split jobs | 41102, 41107, 41109, 41112, 41114, 41117, 41123 |
| Exposure counts | after 24, tp_split 7, driver_new 12, storage_new 14, alert_node 6, tp_x_storage 3 |
| Mean / median of per-job means | 17.38 → 21.42 s (+23.2 %); 17.42 → 19.70 s (+13.1 %); step-weighted +22.3 % |
| Effects ± SE (s/step) | after +0.34 ± 0.09; tp_split +8.96 ± 0.10; driver_new +0.90 ± 0.07; storage_new +1.40 ± 0.07; alert_node −0.05 ± 0.09; tp_x_storage −1.31 ± 0.15; R² = 0.998 |
| Shares of 4.04 s | TP 64.7 %; storage 20.2 %; driver 11.2 %; common shift 8.3 %; interaction −4.0 %; ECC −0.3 %; sum 100 % |
| Bootstrap 95 % (2,000 resamples, seed 22) | common shift 4.2–14.2 % (116 rank-deficient resamples dropped) |
| Storage cross-check | data-wait delta +1.46 s vs coefficient +1.40 s → consistent |
| Test ranking | T3 3.200, T1 1.800, T2 1.400, T4 1.200, T8 0.250, T6 0.117, T7 0.075; rejected T5, T9 |

**Alert verdict.** orion-n13's ECC alert is ruled out: effect −0.05 ± 0.09 s, within one SE of zero;
SBE counts are 140–160 per job-node (jobs run ≈ 1 h, so this is the alert's 140–160/h) with no DBE or row remap and unchanged temperatures.

**Deductions to look for.** Non-time-aware driver flag (driver 0.35 s, after 0.93 s, alert −0.47 s);
additive-only model (alert −0.43 ± 0.14 s, spuriously "significant"; a learner who notices the
implausible negative effect keeps most credit); dropping the failed job; causal words in Measured facts.
