# Lab 8 L2: readiness validator on this host's real inventory, and memory-registration cost

`[MEASURED]` on **CPU fallback: 13th Gen Intel(R) Core(TM) i7-13700HX**, 2026-10-31T23:42:04Z.

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

## Readiness validator on this host's real inventory

Verdict: **NOT_READY**, 9 findings (PEERMEM, PORT_STATE). RDMA devices found: 0.

| Device | Check | Evidence |
|---|---|---|
| mlx5_0 | PORT_STATE | device missing from ibv_devinfo |
| mlx5_1 | PORT_STATE | device missing from ibv_devinfo |
| mlx5_2 | PORT_STATE | device missing from ibv_devinfo |
| mlx5_3 | PORT_STATE | device missing from ibv_devinfo |
| mlx5_4 | PORT_STATE | device missing from ibv_devinfo |
| mlx5_5 | PORT_STATE | device missing from ibv_devinfo |
| mlx5_6 | PORT_STATE | device missing from ibv_devinfo |
| mlx5_7 | PORT_STATE | device missing from ibv_devinfo |
| - | PEERMEM | nvidia_peermem not loaded |

| Inventory section | Source |
|---|---|
| `ibv_devinfo` | command not installed |
| `rdma link show` | command |
| `show_gids` | command not installed |
| `ethtool -i ens1np0` | command |
| `ethtool ens1np0` | command |
| `ip -o link show` | command |
| `ip -o -4 addr show` | command |
| `lsmod \| grep -E 'peermem\|mlx5\|ib_core\|ib_uverbs'` | rendered from /proc/modules (filtered) |
| `cat /etc/halcyon/rdma.env` | file absent |

## Memory registration cost (pinning pages for DMA)

| Method | Size (MiB) | Register median (ms) | p95 (ms) | Deregister median (ms) | us per MiB | n |
|---|---|---|---|---|---|---|
| mlock | 4 | 0.174 | 0.192 | 0.121 | 43.5 | 10 |
| mlock | 64 | 2.594 | 3.200 | 1.821 | 40.5 | 10 |
| mlock | 256 | 11.983 | 13.141 | 7.328 | 46.8 | 10 |
| mlock | 1024 | 56.299 | 66.808 | 33.266 | 55.0 | 10 |

What to conclude:

- A readiness tool is only trustworthy if it fails loudly on a host that cannot do RDMA at all; this one reports every expected rail as missing and the peer-memory module as absent.
- Registration cost grows with the number of pages pinned, so registering per message is expensive. Register once, reuse the memory region, and let NCCL/UCX registration caches do this for you. Unbounded pinning is also why RLIMIT_MEMLOCK (`ulimit -l`) must be raised on RDMA hosts (here: unlimited).
- This is a laptop host in a WSL2 container with no NIC; the RDMA rows of the chapter (perftest bandwidth plateau, p99.9 latency) need the L3 two-host setup.

_CPU fallback: cudaHostRegister and the pinned-versus-pageable copy were not measured; mlock exercises the same kernel page-pinning path._

## Not runnable on this host

- **perftest per rail (ib_write_bw -a --report_gbits, ib_write_lat -a) between two hosts**: needs 2+ hosts with RDMA NICs (RoCEv2 or InfiniBand) on a lab fabric, rdma-core and perftest, root or CAP_NET_ADMIN for dcb/ethtool.
- **Soft-RoCE stand-in (rdma link add rxe0 type rxe netdev <if>)**: needs a kernel with the rdma_rxe module, CAP_NET_ADMIN, a real netdev (the harness runs with --network none).

- Inventory sections are the real command output where the tool exists; ip -o link and lsmod are rendered from /sys/class/net and /proc/modules in those tools' formats (see tables.inventory_provenance).
- The host is labelled l2host-01 because check_node derives the node index from a trailing number.
- Registration timing: perf_counter around each call, 2 warm-ups, then >= 5 repetitions per size; the buffer's pages are touched first so the cost measured is pinning, not page allocation.
