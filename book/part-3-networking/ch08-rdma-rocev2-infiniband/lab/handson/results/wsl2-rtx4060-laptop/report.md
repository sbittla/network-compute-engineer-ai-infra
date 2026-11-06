# Chapter 8 hands-on: Soft-RoCE verbs on 13th Gen Intel(R) Core(TM) i7-13700HX

Kernel 6.18.54.1-rxe+, 24 CPUs; captured 2026-11-05T02:10:48+00:00. One rxe device (`ch08rxe0`) on veth `ch08-v0`; every test is server and client on this host. These are software-RDMA numbers on one CPU, not NIC or fabric numbers.

| Step | Result | Label |
|---|---|---|
| 1 Device | `ch08rxe0` ACTIVE, transport `InfiniBand (0)`, link_layer Ethernet, active_mtu 1024 at netdev MTU 1500 and 4096 at 9000 | `[MEASURED]` |
| 2 GID table | 2 entries, types RoCE v2; IPv4-mapped RoCE v2 GID at index **1** = `0000:0000:0000:0000:0000:ffff:0ad0:0001` (10.208.0.1); ibv_rc_pingpong 73.33 µs/iter | `[MEASURED]` |
| 3 ib_write_bw, path MTU 1024 | plateau 3.59 Gb/s at 32768 B (3 reps: 1.34–3.71), n½ = 2048 B, 2 B rate 0.3059 M msg/s, 65.0 packets per 64 KiB WRITE | `[MEASURED]` |
| 3 ib_write_bw, path MTU 4096 | plateau 9.98 Gb/s at 16384 B (3 reps: 3.32–10.09), n½ = 4096 B, 2 B rate 0.2552 M msg/s, 17.0 packets per 64 KiB WRITE | `[MEASURED]` |
| 4 Latency, 2 B typical | WRITE 10.01 µs, READ 10.55 µs, SEND 21.75 µs; READ/WRITE = 1.05 | `[MEASURED]` |
| 5 Path MTU, 1 MiB WRITEs | 256 B → 0.655 Gb/s (0.32 M pkt/s); 512 B → 1.275 Gb/s (0.311 M pkt/s); 1024 B → 2.26 Gb/s (0.276 M pkt/s); 2048 B → 3.94 Gb/s (0.24 M pkt/s); 4096 B → 5.98 Gb/s (0.182 M pkt/s) | `[MEASURED]` (packet rate derived) |
| 5 Clamp | asked for 4096 at netdev MTU 1500, perftest used 1024 | `[MEASURED]` |
| 6 -d mlx5_0 | rc 1, signature `IB device mlx5_0 not found` found: True | `[MEASURED]` |
| 6 no server | rc 1, signature `Couldn't connect to 10\.208\.0\.1:\d+` found: True | `[MEASURED]` |
| 6 client -x 7 | rc 1, signature `Incompatibility issue with GID types` found: True | `[MEASURED]` |
| 6 both -x 7 | rc 1, signature `Failed to modify QP \S+ to RTR` found: True | `[MEASURED]` |
| 6 -x 0 (link-local GID) | completed: True (loopback only) | `[MEASURED]` |
| 6 Locked memory, 8 MiB buffer | nobody_16384: MR ok; nobody_4096: MR FAILED; nobody_65536: MR ok; nobody_8192: MR FAILED; root_4096: MR ok | `[MEASURED]` |
| 7 Peer killed, timeout=14, retry_cnt 7 | 57 retransmission timeouts, mean interval 0.0683 s (model 0.0671 s); client still waiting: yes | `[MEASURED]` |
| 7 Peer killed, timeout=16, retry_cnt 7 | 27 retransmission timeouts, mean interval 0.2865 s (model 0.2684 s); client still waiting: yes | `[MEASURED]` |
| 7 Peer killed, rdma_cm, retry_cnt 3 | failed after 2.218 s with completion status 12; retry_exceeded_err +1; implied T_ack ≈ 0.5546 s (timeout ≈ 17.05) | `[MEASURED]` |

What carries over to ORION: the verbs objects, GID selection, the path-MTU arithmetic, the failure signatures and the ACK-timeout formula. What does not: every bandwidth and latency number above, which measure one CPU running the transport in software (no NIC, no PCIe, no switch, no PFC).
