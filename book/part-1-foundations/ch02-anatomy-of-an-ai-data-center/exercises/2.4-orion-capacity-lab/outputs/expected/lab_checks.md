# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `data_regenerates_identically` | PASS data_regenerates_identically: 6 files byte-identical |
| `validate_rack_plan` | PASS validate_rack_plan: 4 rack-plan flaws detected |
| `validate_fabric_plan` | PASS validate_fabric_plan: 3 fabric-plan flaws detected |
| `validate_storage_and_node` | PASS validate_storage_and_node: storage unit and PSU feed-loss flaws detected |
| `validate_no_false_positives` | PASS validate_no_false_positives: no false positives |
| `bom_counts` | PASS bom_counts: servers, RUs, switches, ports and links correct |
| `bom_optics_frontend_oob` | PASS bom_optics_frontend_oob: optics, frontend and OOB counts correct |
| `rack_power_budget` | PASS rack_power_budget: rack max 41.0 kW, design 45.1 kW, 65.6 kW usable per side |
| `rack_cooling_budget` | PASS rack_cooling_budget: coolant 46.4 L/min, residual air ~1,200 CFM, CDU 82 % loaded |
| `cluster_power_energy` | PASS cluster_power_energy: cluster 382 kW IT max, ~3,587 MWh/yr |
| `capacity_compute_fabric` | PASS capacity_compute_fabric: HBM, per-GPU training state and bisection correct |
| `capacity_storage_utilization` | PASS capacity_storage_utilization: storage per GPU, checkpoint lower bound and GPU-hours correct |
| `spof_set` | PASS spof_set: 15 SPOFs found (incl. hidden power-path SPOFs) |
| `spof_service_impact` | PASS spof_service_impact: service impact per SPOF correct |
