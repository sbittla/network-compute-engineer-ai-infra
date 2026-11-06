# Marking scheme: 12.13 nccl-tests analysis toolkit (lab)

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** checker output (10/10 PASS), summary table, anomaly labels with explanations, and (optional) your gloo log labelled `[MEASURED]` with the environment.

| Criterion | Points |
|---|---|
| bus_factor, parse_nccl_log and compute_bw pass | 25 |
| plateau_busbw, classify_regions and fit_alpha_beta pass | 30 |
| jitter_cv, analyze_all and predict_time_us pass | 25 |
| detect_anomalies passes and the labels are explained (c3 low_plateau_steady, c6 low_plateau_jittery) | 15 |
| Summary table and evidence labels correct; optional gloo log with environment if submitted | 5 |
