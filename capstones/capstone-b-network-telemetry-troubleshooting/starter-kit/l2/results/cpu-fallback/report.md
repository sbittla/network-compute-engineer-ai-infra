# Capstone B L2: real counter collection, L1 rate pipeline and Prometheus exposition

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-11-01T00:12:18Z.

| Environment | Value |
|---|---|
| device | cpu |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |

**Status:** ran
**Invariants:** all passed

## What exists on this host

RDMA devices: none; interfaces: ['lo']; ethtool: True; rdma: True; mlnx_qos: False.

Collector output (first block, bundle format):

```text
### collected_at=1793491939 host=e916fe3cc22f dev=lo netdev=lo rail=-
     rx_bytes: 43356996
     tx_bytes: 43356996
     rx_packets: 1985
     tx_packets: 1985
     rx_dropped: 0
     tx_dropped: 0
```

## L1 pipeline on real counters (`instructor/reference/telemetry.py`)

- `parse_nic_ethtool` with the stock map: **0 rows**. None of the native names here (rx_bytes, rx_dropped, rx_packets, tx_bytes, tx_dropped, tx_packets) are mlx5 names.
- With a host adapter map {'tx_bytes': 'tx_bytes', 'rx_bytes': 'rx_bytes', 'rx_dropped': 'rx_discards', 'tx_dropped': 'tx_discards'}: 124 rows, canonical counters ['rx_bytes', 'rx_discards', 'tx_bytes', 'tx_discards'].
- `compute_rates`: 0 invalid intervals.

| Interval | dt (s) | L1 rate (MB/s) | counter delta (B) | app bytes | packets | overhead (B/pkt) |
|---|---|---|---|---|---|---|
| 1 | 1 | 200.4 | 200397656 | 200015872 | 7342 | 52.0 |
| 2 | 1 | 200.3 | 200263808 | 200015872 | 4768 | 52.0 |
| 3 | 1 | 200.3 | 200254968 | 200015872 | 4598 | 52.0 |
| 4 | 1 | 200.3 | 200253928 | 200015872 | 4578 | 52.0 |
| 5 | 1 | 200.3 | 200253928 | 200015872 | 4578 | 52.0 |
| 6 | 1 | 200.3 | 200254084 | 200015872 | 4581 | 52.0 |
| 7 | 1 | 200.3 | 200293136 | 200015872 | 5332 | 52.0 |
| 8 | 1 | 200.3 | 200287052 | 200015872 | 5215 | 52.0 |
| 9 | 1 | 200.3 | 200259648 | 200015872 | 4688 | 52.0 |
| 10 | 1 | 201.0 | 201046756 | 200802304 | 4701 | 52.0 |
| 11 | 1 | 200.5 | 200523508 | 200278016 | 4721 | 52.0 |
| 12 | 1 | 200.0 | 199998128 | 199753728 | 4700 | 52.0 |
| 13 | 1 | 200.3 | 200258660 | 200015872 | 4669 | 52.0 |
| 14 | 1 | 200.3 | 200261156 | 200015872 | 4717 | 52.0 |
| 15 | 1 | 200.5 | 200525120 | 200278016 | 4752 | 52.0 |
| 16 | 1 | 200.0 | 199995632 | 199753728 | 4652 | 52.0 |
| 17 | 1 | 200.3 | 200258088 | 200015872 | 4658 | 52.0 |
| 18 | 1 | 200.3 | 200259856 | 200015872 | 4692 | 52.0 |
| 19 | 1 | 200.3 | 200259596 | 200015872 | 4687 | 52.0 |
| 20 | 1 | 200.3 | 200258868 | 200015872 | 4673 | 52.0 |
| 21 | 1 | 200.3 | 200259232 | 200015872 | 4680 | 52.0 |
| 22 | 1 | 200.3 | 200257776 | 200015872 | 4652 | 52.0 |
| 23 | 1 | 200.3 | 200260532 | 200015872 | 4705 | 52.0 |
| 24 | 1 | 200.3 | 200258140 | 200015872 | 4659 | 52.0 |
| 25 | 1 | 200.3 | 200258608 | 200015872 | 4668 | 52.0 |
| 26 | 1 | 200.0 | 199995580 | 199753728 | 4651 | 52.0 |
| 27 | 1 | 200.5 | 200521792 | 200278016 | 4688 | 52.0 |
| 28 | 1 | 200.3 | 200260064 | 200015872 | 4696 | 52.0 |
| 29 | 1 | 200.0 | 199997660 | 199753728 | 4691 | 52.0 |
| 30 | 1 | 200.3 | 200259492 | 200015872 | 4685 | 52.0 |

32-bit replay: 1 wrap(s) across 30 intervals; `counter_delta(prev, cur, 32)` recovered every true delta exactly: **True**.

## Prometheus exposition (last scrape)

```text
# HELP node_network_transmit_bytes_total Bytes transmitted (kernel interface counter).
# TYPE node_network_transmit_bytes_total counter
node_network_transmit_bytes_total{device="lo"} 6051849448
# HELP node_network_receive_bytes_total Bytes received (kernel interface counter).
# TYPE node_network_receive_bytes_total counter
node_network_receive_bytes_total{device="lo"} 6051849448
# HELP node_network_transmit_packets_total Packets transmitted.
# TYPE node_network_transmit_packets_total counter
node_network_transmit_packets_total{device="lo"} 146062
# HELP node_network_receive_drop_total Received packets dropped.
# TYPE node_network_receive_drop_total counter
node_network_receive_drop_total{device="lo"} 0
# HELP process_cpu_seconds_total Collector process CPU time.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 10.0809
# HELP collector_scrape_duration_seconds Time the collector spent producing this scrape.
# TYPE collector_scrape_duration_seconds gauge
collector_scrape_duration_seconds 0.000314
```

Re-parsed 31 scrapes: 0 format problems, counters monotonic: True.

| Collector step | median (ms) | p95 (ms) |
|---|---|---|
| sysfs interface counters | 0.391 | 0.708 |

## Not runnable here

- **RDMA NIC hw_counters (np_cnp_sent, rp_cnp_handled, out_of_sequence, ...) and ethtool -S on an mlx5 netdev**. Probe: /sys/class/infiniband=none; interfaces=['lo']; ethtool=True. Needs: host with an mlx5-class RDMA NIC, root for ethtool/sysfs reads. Fallback: kernel loopback counters collected in the same native format.
- **PFC/ECN configuration (mlnx_qos) and rdma statistic**. Probe: mlnx_qos=False, rdma=True. Needs: vendor NIC tools. Fallback: none.
- **L3: switch streaming telemetry (gNMI) and incast with ECN disabled**. Probe: gnmic=False, single host. Needs: 2+ RDMA hosts, lab switch with PFC/ECN. Fallback: none.

## What to conclude

- A parser validated only on the simulated bundle returns *nothing* on a new driver. That is silent, and worse than an error. Record the native names each driver/firmware exposes, and map them explicitly.
- Interface byte counters include headers: here ~52.0 B per packet on top of the application bytes. Compare like with like before calling a rate 'wrong'.
- Wrap handling is only correct if the counter width is known per native name (device_profiles.yaml). A 64-bit assumption on a 32-bit counter turns every wrap into a fake reset or a negative rate.
- _CPU fallback: no GPU was used. GPU metrics and their physical-range invariants were skipped._

- Polls aligned to whole seconds (collected_at is integer epoch seconds, as in the bundle).
- Traffic: one TCP stream over 127.0.0.1, rate-limited to 200 MB/s of application bytes.
- The 32-bit wrap test replays the real tx_bytes series modulo 2^32 with an offset; the wrap is synthetic, the deltas are real.
