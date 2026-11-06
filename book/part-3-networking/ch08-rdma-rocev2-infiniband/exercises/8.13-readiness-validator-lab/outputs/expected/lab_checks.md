# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `parse_ibv_devinfo: fields parsed` | PASS parse_ibv_devinfo: fields parsed |
| `parse_rdma_link: state/physical_state/netdev parsed` | PASS parse_rdma_link: state/physical_state/netdev parsed |
| `parse_show_gids: v1/v2 and IPv4 columns parsed` | PASS parse_show_gids: v1/v2 and IPv4 columns parsed |
| `parse_ethtool: driver/firmware/speed parsed` | PASS parse_ethtool: driver/firmware/speed parsed |
| `parse_ip: MTU/state/addresses parsed` | PASS parse_ip: MTU/state/addresses parsed |
| `parse_qos_env_lsmod: dcb, env file and lsmod parsed` | PASS parse_qos_env_lsmod: dcb, env file and lsmod parsed |
| `no_false_positive_clean_node: orion-n01 passes every check (no false positives)` | PASS no_false_positive_clean_node: orion-n01 passes every check (no false positives) |
| `readiness_findings: all 18 planted-fault findings detected, no extras` | PASS readiness_findings: all 18 planted-fault findings detected, no extras |
| `node_verdicts: per-node READY/NOT_READY verdicts correct` | PASS node_verdicts: per-node READY/NOT_READY verdicts correct |
| `render_report: report rendered (35 lines)` | PASS render_report: report rendered (35 lines) |
| `parse_perftest: bw/lat tables parsed; plateau and n1/2 computed` | PASS parse_perftest: bw/lat tables parsed; plateau and n1/2 computed |
| `perftest_summary: 32 rows, fleet median plateau 388.6 Gb/s` | PASS perftest_summary: 32 rows, fleet median plateau 388.6 Gb/s |
| `perftest_flags: underperforming pair and tail-latency pair flagged` | PASS perftest_flags: underperforming pair and tail-latency pair flagged |
| `pcie_correlation: PCIe downgrade correlated` | PASS pcie_correlation: PCIe downgrade correlated |
| `data_regenerates_identically: generator reproduces data/ byte-for-byte` | PASS data_regenerates_identically: generator reproduces data/ byte-for-byte |
