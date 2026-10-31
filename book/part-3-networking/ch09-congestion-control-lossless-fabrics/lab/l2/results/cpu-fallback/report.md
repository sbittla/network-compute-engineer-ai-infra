# Lab 9 L2: RDMA-counter probe, host-stack N:1 incast and real ECN/retransmit counters

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:42:19Z.

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

## Host congestion-control configuration (read now)

TCP congestion control **cubic** (available: reno cubic); `tcp_ecn` = **2** (0 off, 1 request ECN, 2 accept ECN only when the peer requests it). RDMA devices: 0; interfaces: ['lo'].

## N:1 incast on loopback `[MEASURED, host stack only]`

| Senders | Per-flow Gb/s (median) | Per-flow p5 | FCT median (ms) | FCT p95 | FCT p99 | Incast completion (ms) | Aggregate Gb/s | Jain (median / min) |
|---|---|---|---|---|---|---|---|---|
| 1 | 34.2 | 21.5 | 31.4 | 49.9 | 49.9 | 31.4 | 34.2 | 1.000 / 1.000 |
| 2 | 33.9 | 26.9 | 31.7 | 39.9 | 40.6 | 31.8 | 67.7 | 1.000 / 0.998 |
| 4 | 28.3 | 23.3 | 37.9 | 46.0 | 48.1 | 38.5 | 111.7 | 1.000 / 0.998 |
| 8 | 10.3 | 9.5 | 104.7 | 112.7 | 115.0 | 107.0 | 80.3 | 0.999 / 0.999 |

Counter deltas over all runs: IpExt.InCEPkts +0, IpExt.InECT0Pkts +0, IpExt.InECT1Pkts +0, IpExt.InNoECTPkts +446705, Tcp.InSegs +446670, Tcp.OutSegs +446699, Tcp.RetransSegs +6, TcpExt.TCPBacklogDrop +0, TcpExt.TCPFastRetrans +6, TcpExt.TCPLossProbes +0, TcpExt.TCPRcvQDrop +0, TcpExt.TCPSpuriousRTOs +0, TcpExt.TCPTimeouts +0.

Counter rates per run (events/s, via the lab's `counters_to_rates`):

| Run | Tcp.InSegs | Tcp.OutSegs | Tcp.RetransSegs | TcpExt.TCPFastRetrans | TcpExt.TCPTimeouts | TcpExt.TCPLossProbes | TcpExt.TCPSpuriousRTOs | TcpExt.TCPBacklogDrop | TcpExt.TCPRcvQDrop | IpExt.InNoECTPkts | IpExt.InECT1Pkts | IpExt.InECT0Pkts | IpExt.InCEPkts |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N1 | 136919 | 136928 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 136928 | 0 | 0 | 0 |
| N2 | 231793 | 231798 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 231798 | 0 | 0 | 0 |
| N4 | 182614 | 182626 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 182626 | 0 | 0 | 0 |
| N8 | 153263 | 153272 | 5 | 5 | 0 | 0 | 0 | 0 | 0 | 153277 | 0 | 0 | 0 |

## The lab's 400 Gb/s incast model for comparison `[SIMULATED]`

| Config | Completion (us) | Peak queue (KB) | Pause time (us) | Dropped bytes | CNPs |
|---|---|---|---|---|---|
| A_as_found | 960 | 1660 | 863 | 0 | 0 |
| B_template | 1257 | 1660 | 114 | 0 | 60 |
| C_lossy | 3875 | 4000 | 0 | 17840000 | 84 |

What to conclude:

- With 8 senders sharing one receiver, each flow got 10.3 Gb/s against 34.2 Gb/s alone, and the p99 FCT is the number a collective waits for. Report per-flow percentiles and fairness, never only the aggregate.
- ECN-capable packets 0, CE marks 0, retransmits 6: with `tcp_ecn=2` and no marking queue, nothing on this path can signal congestion early. On a RoCE fabric that signal is ECN at the switch and CNPs at the NIC; reading those counters as rates is exactly what the L2 extension asks for once an RDMA NIC is present.
- The FCT tail stayed within 1.6x of the median at every N: no retransmission-driven tail on this run.
- This is a laptop in a WSL2 container: loopback has no switch buffer, so queue build-up, PFC pauses and the ECN-threshold effect in the simulated table cannot be measured here. Those need the L3 lab fabric.

## Not runnable on this host

- **RDMA NIC congestion counters (PFC pause, np_cnp_sent, rp_cnp_handled, np_ecn_marked_roce_packets) sampled 60 s apart**: needs an RDMA-capable NIC (mlx5-class or similar), ethtool / rdma-core, a real netdev (the harness runs with --network none).
- **L3 N:1 RDMA incast with switch queue watermarks, ECN threshold A/B on a lab leaf**: needs >= 4 hosts with RoCEv2 NICs on one lab leaf, switch CLI/telemetry access, perftest.

- Incast: N sender threads each send 128 MiB over loopback TCP to one receiver; 1 warm-up (1/8 size) and 10 timed repetitions per N; FCT measured at the receiver from a common start.
- Loopback has no egress queue, no ECN marking and no PFC: the shared bottleneck is the receiver's CPU and socket stack. Treat the numbers as host-stack behaviour, not fabric behaviour.
- Counter rates: solutions/lab/congestion_lab.py. Simulation: solutions/lab/congestion_lab.py: compare_configs (0.6 s).
