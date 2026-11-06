# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `data_determinism` | PASS data_determinism       regenerated data is byte-identical |
| `rates_unit` | PASS rates_unit             first sample NaN, gap divided by true elapsed time, reset -> NaN |
| `rates_dataset` | PASS rates_dataset          no negative rates across 9588 samples |
| `episode_count` | PASS episode_count          3 episodes |
| `episode_labels` | PASS episode_labels         3 episodes, labels at probe times match |
| `congestion_roots` | PASS congestion_roots       congestion-tree roots correct |
| `storm_source` | PASS storm_source           storm source orion-n12:mlx5_3 |
| `victim_flows` | PASS victim_flows           3 victim (probe, episode) pairs |
| `qos_audit` | PASS qos_audit              4 configuration findings |
| `red_profile` | PASS red_profile            RED/ECN profile correct |
| `sim_conservation` | PASS sim_conservation       bytes conserved; no config beats the line-rate lower bound |
| `sim_lossless_configs` | PASS sim_lossless_configs   PFC configs lose nothing and stay within headroom |
| `sim_compare_A_vs_B` | PASS sim_compare_A_vs_B     template ECN cuts pause exposure 862.8 -> 113.6 us (CNPs 0 -> 60) |
| `sim_lossy_config` | PASS sim_lossy_config       lossy config drops 17840000 B and finishes later |
| `report_sections` | PASS report_sections        report has all 9 sections |
