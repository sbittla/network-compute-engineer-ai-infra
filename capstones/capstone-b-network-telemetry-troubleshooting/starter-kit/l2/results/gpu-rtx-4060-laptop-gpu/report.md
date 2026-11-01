# Capstone B L2: real counter collection, L1 rate pipeline and Prometheus exposition

`[MEASURED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-11-01T00:11:43Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

## What exists on this host

RDMA devices: none; interfaces: ['lo']; ethtool: True; rdma: True; mlnx_qos: False.

Collector output (first block, bundle format):

```text
### collected_at=1793491904 host=b182c08eb134 dev=lo netdev=lo rail=-
     rx_bytes: 53079724
     tx_bytes: 53079724
     rx_packets: 2435
     tx_packets: 2435
     rx_dropped: 0
     tx_dropped: 0
```

## L1 pipeline on real counters (`instructor/reference/telemetry.py`)

- `parse_nic_ethtool` with the stock map: **0 rows**. None of the native names here (rx_bytes, rx_dropped, rx_packets, tx_bytes, tx_dropped, tx_packets) are mlx5 names.
- With a host adapter map {'tx_bytes': 'tx_bytes', 'rx_bytes': 'rx_bytes', 'rx_dropped': 'rx_discards', 'tx_dropped': 'tx_discards'}: 124 rows, canonical counters ['rx_bytes', 'rx_discards', 'tx_bytes', 'tx_discards'].
- `compute_rates`: 0 invalid intervals.

| Interval | dt (s) | L1 rate (MB/s) | counter delta (B) | app bytes | packets | overhead (B/pkt) |
|---|---|---|---|---|---|---|
| 1 | 1 | 200.5 | 200493856 | 200015872 | 9192 | 52.0 |
| 2 | 1 | 200.5 | 200494064 | 200015872 | 9196 | 52.0 |
| 3 | 1 | 200.3 | 200346176 | 200015872 | 6352 | 52.0 |
| 4 | 1 | 200.0 | 200004628 | 199753728 | 4825 | 52.0 |
| 5 | 1 | 200.5 | 200523248 | 200278016 | 4717 | 52.0 |
| 6 | 1 | 200.0 | 199998284 | 199753728 | 4702 | 52.0 |
| 7 | 1 | 200.3 | 200261936 | 200015872 | 4732 | 52.0 |
| 8 | 1 | 200.5 | 200528292 | 200278016 | 4813 | 52.0 |
| 9 | 1 | 200.3 | 200260532 | 200015872 | 4705 | 52.0 |
| 10 | 1 | 200.0 | 199998648 | 199753728 | 4710 | 52.0 |
| 11 | 1 | 200.3 | 200259544 | 200278016 | 4687 | -3.9 |
| 12 | 1 | 200.3 | 200261728 | 199753728 | 4727 | 107.5 |
| 13 | 1 | 200.3 | 200261728 | 200015872 | 4728 | 52.0 |
| 14 | 1 | 200.3 | 200261936 | 200015872 | 4735 | 52.0 |
| 15 | 1 | 201.1 | 201051956 | 200802304 | 4798 | 52.0 |
| 16 | 1 | 200.3 | 200260428 | 200015872 | 4703 | 52.0 |
| 17 | 1 | 200.0 | 199999376 | 199753728 | 4724 | 52.0 |
| 18 | 1 | 200.5 | 200525016 | 200278016 | 4750 | 52.0 |
| 19 | 1 | 200.3 | 200262716 | 200540160 | 4754 | -58.4 |
| 20 | 1 | 200.3 | 200261884 | 199491584 | 4724 | 163.1 |
| 21 | 1 | 200.3 | 200259752 | 200015872 | 4690 | 52.0 |
| 22 | 1 | 200.0 | 200020904 | 200015872 | 5145 | 1.0 |
| 23 | 1 | 200.5 | 200527564 | 200015872 | 4793 | 106.8 |
| 24 | 1 | 200.3 | 200263704 | 200015872 | 4765 | 52.0 |
| 25 | 1 | 200.0 | 200000000 | 199753728 | 4736 | 52.0 |
| 26 | 1 | 200.3 | 200262560 | 200015872 | 4744 | 52.0 |
| 27 | 1 | 200.3 | 200261052 | 200015872 | 4715 | 52.0 |
| 28 | 1 | 200.3 | 200268124 | 200015872 | 4851 | 52.0 |
| 29 | 1 | 200.3 | 200261052 | 200015872 | 4715 | 52.0 |
| 30 | 1 | 200.3 | 200260688 | 200015872 | 4708 | 52.0 |

32-bit replay: 1 wrap(s) across 30 intervals; `counter_delta(prev, cur, 32)` recovered every true delta exactly: **True**.

## Prometheus exposition (last scrape)

```text
# HELP node_network_transmit_bytes_total Bytes transmitted (kernel interface counter).
# TYPE node_network_transmit_bytes_total counter
node_network_transmit_bytes_total{device="lo"} 6061781100
# HELP node_network_receive_bytes_total Bytes received (kernel interface counter).
# TYPE node_network_receive_bytes_total counter
node_network_receive_bytes_total{device="lo"} 6061781100
# HELP node_network_transmit_packets_total Packets transmitted.
# TYPE node_network_transmit_packets_total counter
node_network_transmit_packets_total{device="lo"} 155571
# HELP node_network_receive_drop_total Received packets dropped.
# TYPE node_network_receive_drop_total counter
node_network_receive_drop_total{device="lo"} 0
# HELP process_cpu_seconds_total Collector process CPU time.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 26.2474
# HELP gpu_power_watts Board power draw (nvidia-smi power.draw).
# TYPE gpu_power_watts gauge
gpu_power_watts{gpu="0"} 60.52
# HELP gpu_sm_clock_hertz SM clock.
# TYPE gpu_sm_clock_hertz gauge
gpu_sm_clock_hertz{gpu="0"} 2520000000
# HELP gpu_temperature_celsius GPU core temperature.
# TYPE gpu_temperature_celsius gauge
gpu_temperature_celsius{gpu="0"} 76.0
# HELP gpu_utilization_ratio Fraction of time a kernel was running.
# TYPE gpu_utilization_ratio gauge
gpu_utilization_ratio{gpu="0"} 0.59
# HELP gpu_clock_event_reason_active 1 if the clock-event reason is active now.
# TYPE gpu_clock_event_reason_active gauge
gpu_clock_event_reason_active{gpu="0",reason="idle"} 0
gpu_clock_event_reason_active{gpu="0",reason="sw_power_cap"} 0
gpu_clock_event_reason_active{gpu="0",reason="hw_slowdown"} 0
gpu_clock_event_reason_active{gpu="0",reason="sw_thermal"} 0
gpu_clock_event_reason_active{gpu="0",reason="hw_thermal"} 0
gpu_clock_event_reason_active{gpu="0",reason="hw_power_brake"} 0
# HELP gpu_clock_event_reason_seconds_total Cumulative time clocks were held by a reason.
# TYPE gpu_clock_event_reason_seconds_total counter
gpu_clock_event_reason_seconds_total{gpu="0",reason="hw_power_braking"} 0.0
gpu_clock_event_reason_seconds_total{gpu="0",reason="hw_thermal_slowdown"} 0.0
gpu_clock_event_reason_seconds_total{gpu="0",reason="sw_power_capping"} 0.076926
gpu_clock_event_reason_seconds_total{gpu="0",reason="sw_thermal_slowdown"} 0.0
gpu_clock_event_reason_seconds_total{gpu="0",reason="sync_boost"} 0.0
# HELP collector_scrape_duration_seconds Time the collector spent producing this scrape.
# TYPE collector_scrape_duration_seconds gauge
collector_scrape_duration_seconds 0.21077
```

Re-parsed 31 scrapes: 0 format problems, counters monotonic: True.

| Collector step | median (ms) | p95 (ms) |
|---|---|---|
| sysfs interface counters | 0.285 | 0.800 |
| nvidia-smi query + PERFORMANCE counters | 163.1 | 229.7 |

## Not runnable here

- **RDMA NIC hw_counters (np_cnp_sent, rp_cnp_handled, out_of_sequence, ...) and ethtool -S on an mlx5 netdev**. Probe: /sys/class/infiniband=none; interfaces=['lo']; ethtool=True. Needs: host with an mlx5-class RDMA NIC, root for ethtool/sysfs reads. Fallback: kernel loopback counters collected in the same native format.
- **PFC/ECN configuration (mlnx_qos) and rdma statistic**. Probe: mlnx_qos=False, rdma=True. Needs: vendor NIC tools. Fallback: none.
- **L3: switch streaming telemetry (gNMI) and incast with ECN disabled**. Probe: gnmic=False, single host. Needs: 2+ RDMA hosts, lab switch with PFC/ECN. Fallback: none.

## What to conclude

- A parser validated only on the simulated bundle returns *nothing* on a new driver. That is silent, and worse than an error. Record the native names each driver/firmware exposes, and map them explicitly.
- Interface byte counters include headers: here ~52.0 B per packet on top of the application bytes. Compare like with like before calling a rate 'wrong'.
- Wrap handling is only correct if the counter width is known per native name (device_profiles.yaml). A 64-bit assumption on a 32-bit counter turns every wrap into a fake reset or a negative rate.
- Each nvidia-smi scrape costs ~163.1 ms of wall time (p95 229.7 ms). For sub-second telemetry use a resident agent (DCGM exporter, NVML), not a process per poll. This is a laptop Ada GPU, not an H100 node.

- Polls aligned to whole seconds (collected_at is integer epoch seconds, as in the bundle).
- Traffic: one TCP stream over 127.0.0.1, rate-limited to 200 MB/s of application bytes.
- The 32-bit wrap test replays the real tx_bytes series modulo 2^32 with an offset; the wrap is synthetic, the deltas are real.
