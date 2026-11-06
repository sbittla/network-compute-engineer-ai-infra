# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `clean_steps: dedupe + warm-up` | PASS clean_steps: dedupe + warm-up - 8990 rows after cleaning (expected 8990), 0 duplicate job-steps, min step 10 |
| `tp_split_jobs: TP groups spanning nodes` | PASS tp_split_jobs: TP groups spanning nodes - 7 TP-split jobs found; missing [], extra [] |
| `job_factor_table: time-aware factor flags` | PASS job_factor_table: time-aware factor flags - factor exposure counts match |
| `job_factor_table: failed job retained` | PASS job_factor_table: failed job retained - job 41114 has 60 usable steps (expected 60) |
| `regression_summary: mean vs median change` | PASS regression_summary: mean vs median change - before 17.38 s, after 21.42 s, mean +23.2 % (exp 23.2), median +13.1 % (exp 13.1), step-weighted +22.3 % (exp 22.3) |
| `estimate_effects: per-factor OLS effects` | PASS estimate_effects: per-factor OLS effects - all six model terms within tolerance |
| `attribute: contributions and shares` | PASS attribute: contributions and shares - contributions sum 4.04 s vs delta 4.04 s; share issues none; share SE ok=True, HC3 ok=True |
| `bootstrap_shares: job-level 95 % interval` | PASS bootstrap_shares: job-level 95 % interval - common-shift share 8.3 %, bootstrap 95 % [4.2, 14.2] (exp ~[4, 14]), 1884 resamples used |
| `storage_crosscheck: direct vs inferred` | PASS storage_crosscheck: direct vs inferred - data-wait delta 1.46 s vs storage coef 1.40 s, consistent=True |
| `rank_tests: value/cost/risk ordering + safety` | PASS rank_tests: value/cost/risk ordering + safety - order ['T3', 'T1', 'T2', 'T4', 'T8', 'T6', 'T7']; rejected ['T5', 'T9'] |
| `render_report: facts / causes / uncertainty` | PASS render_report: facts / causes / uncertainty - report has hygiene counts (44 duplicates, 480 warm-up rows, 0 jobs dropped) and ordered sections |
