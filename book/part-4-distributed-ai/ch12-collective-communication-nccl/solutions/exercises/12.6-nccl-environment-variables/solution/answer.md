# 12.6 — NCCL environment variables

Section 12.7, Table 12.5 `[VENDOR-SPEC, 2026-10]`. The rule: production templates set only
*platform facts* (which devices, which interface, which GID); *tuning overrides* stay out unless a
measurement proves they help on that platform and release.

| Variable | Controls | In a production job template? |
|---|---|---|
| `NCCL_DEBUG` | Log verbosity (`WARN`, `INFO`, `TRACE`) | Yes, at `WARN`; `INFO` only for start-up diagnosis (verbose, but cheap to enable for one run) |
| `NCCL_DEBUG_SUBSYS` | Which subsystems log at INFO (`INIT`, `NET`, `GRAPH`, `TUNING`, `ENV`, …) | Only together with INFO, for diagnosis |
| `NCCL_IB_HCA` | Which RDMA devices/ports NCCL may use | Yes if needed, set by the platform team and validated per node type; a wrong list silently halves bandwidth (lab c3) |
| `NCCL_SOCKET_IFNAME` | Interface for bootstrap and the socket transport | Yes on multi-homed hosts (pick the management/frontend interface explicitly) |
| `NCCL_ALGO` | Restricts algorithms (Ring, Tree, NVLS, CollNet…) | No — diagnosis only; a leftover `Ring` doubles small-message latency (12.14) |
| `NCCL_PROTO` | Restricts protocols (LL, LL128, Simple) | No — diagnosis only |
| `NCCL_TOPO_DUMP_FILE` | Writes the topology NCCL detected (XML) | Acceptable (cheap, useful evidence) or diagnosis only |
| `NCCL_IB_GID_INDEX` | RoCEv2 GID index (RoCE version and IP family) | Yes, one platform-wide value, when auto-selection is not reliable on that fabric |

**Common mistakes.** Copying `NCCL_ALGO`/`NCCL_PROTO` from a forum post into an image; setting
`NCCL_DEBUG=INFO` permanently and drowning logs; letting each team set `NCCL_IB_HCA` differently.
A lint that rejects tuning overrides in production images is a cheap guard.
