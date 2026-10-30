# Telemetry Schema

## 1. Normalized sample (long format)

| Field | Type | Unit / encoding | Meaning | Lineage |
|---|---|---|---|---|
| ts | timestamp | UTC, tz-aware | Poll time reported by the source | leaf: `Timestamp:` ISO-8601; spine: `timestamp_ns`; NIC: `collected_at` (s) |
| device | string | hostname | <fill> | <fill> |
| interface | string | <fill> | <fill: switch port name or RDMA device name> | <fill> |
| counter | enum | canonical name | <fill> | mapping table below |
| native | string | | Name in the source format, kept for lineage and width lookup | |
| value | uint64 | count / bytes | Cumulative counter value | |
| source | enum | leaf_cli / spine_stream / nic_ethtool | <fill> | |

## 2. Canonical counters

| Canonical | Unit | Leaf CLI | Spine JSON | NIC (`ethtool -S` / hw_counters) | Direction semantics |
|---|---|---|---|---|---|
| rx_bytes | bytes | <fill> | <fill> | <fill> | <fill: received by this interface> |
| tx_bytes | bytes | | | | |
| rx_discards | packets | | | | |
| tx_discards | packets | | | | |
| fcs_errors | frames | | | | |
| fec_corrected | codewords | | | | |
| fec_uncorrectable | codewords | | | | |
| pfc_rx_pause_p3 | frames | | | | <fill: pause frames *received* (the peer asked us to stop)> |
| pfc_tx_pause_p3 | frames | | | | <fill: pause frames *sent* (we asked the peer to stop)> |
| ecn_marked_p3 | packets | <fill> | <fill> | — | Switch: packets CE-marked on egress by this port |
| ecn_ce_received_p3 | packets | — | — | <fill: np_ecn_marked_roce_packets> | NIC as notification point: CE-marked RoCE packets received (triggers CNPs) |
| cnp_sent | packets | — | — | | |
| cnp_handled | packets | — | — | | |
| out_of_sequence | events | — | — | | |
| local_ack_timeout_err | events | — | — | | |

## 3. Counter widths, wraps and resets

| Platform | Default width | Exceptions | Source of truth |
|---|---|---|---|
| <fill> | | | `device_profiles.yaml`; vendor docs `[VENDOR-SPEC, YYYY-MM]` |

Policy: <fill: how you compute deltas; how you tell a wrap from a reset — which discontinuity signal
(device uptime, boot ID, counter-discontinuity time) you would use in production, and the plausibility
bound (max rate × dt) you use on this capture; what happens to the interval after a reset; why you never
substitute 0>.

## 4. Derived metrics

| Metric | Formula | Unit | Used by |
|---|---|---|---|
| rate | delta / dt (real dt from timestamps) | units/s | all rules |
| uplink CV | std / mean of uplink tx_bytes rates per leaf per interval | — | ecmp_imbalance |
| <fill> | | | |

## 5. Time alignment

<fill: how you align 60 s switch polls with 120 s NIC polls and jittered timestamps; what you do
about clock skew.>
