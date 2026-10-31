# 8.12 — Pre-deployment readiness checklist (model answer)

Relies on manuscript "Production operations notes" (Table 8.10, the chapter's deliverable checklist),
Sections 8.7, 8.8 and 8.10, and docs/VERIFIED_FACTS.md (GPUDirect RDMA validation, locked memory).
Thresholds are `[ILLUSTRATIVE]`. "Automated in lab" means Lab 8's `check_node` covers it.

| # | Item | Command / data source | Pass criterion | Read-only | Automated in lab |
|---|---|---|---|---|---|
| 1 | Devices present, mapped to netdevs | `rdma link show`, `ibv_devices` | `mlx5_0`–`mlx5_7` ↔ baseline netdevs | yes | yes |
| 2 | Port state | `ibv_devinfo`, `rdma link` | `PORT_ACTIVE` / `LINK_UP` on all 8 | yes | yes (PORT_STATE) |
| 3 | Link layer and speed | `ibv_devinfo`, `ethtool <if>` | `Ethernet`, `400000Mb/s` | yes | yes (LINK_LAYER, LINK_SPEED) |
| 4 | NIC firmware | `ibv_devinfo` `fw_ver`, `ethtool -i` | Equals baseline for the PSID | yes | yes (FIRMWARE) |
| 5 | Driver / RDMA stack | `ethtool -i`, package versions | Equals baseline; inside the vendor matrix | yes | yes (DRIVER) |
| 6 | Netdev MTU and `active_mtu` | `ip -o link`, `ibv_devinfo` | 9000; `active_mtu 4096 (5)` | yes | yes (MTU) |
| 7 | Address plan | `ip -o -4 addr` | `10.100.r.(2n+1)/31` on the rail *r* NIC | yes | yes (ADDRESS_PLAN) |
| 8 | GID index | env file, `show_gids` / sysfs | Index is `RoCE v2` and holds the rail IP on every NIC | yes | yes (GID_INDEX) |
| 9 | DSCP trust and map | `dcb apptrust show dev <if>`, `dcb app show dev <if> dscp-prio` | Trust DSCP; 26 → prio 3, 48 → prio 6 | yes | map yes (QOS_DSCP); trust no |
| 10 | PFC priorities | `dcb pfc show dev <if> prio-pfc` | Priority 3 only | yes | yes (QOS_PFC) |
| 11 | Traffic-class marking | site env file | `NCCL_IB_TC=106` | yes | no (good extension) |
| 12 | GPUDirect RDMA mechanism present | `lsmod` (`nvidia_peermem`) or DMA-BUF support | Present. Necessary, not sufficient | yes | yes (PEERMEM) |
| 13 | NIC PCIe link | `lspci -vv -s <bdf>` | `LnkSta` = `LnkCap` (32GT/s, x16) | yes | correlation only (perftest) |
| 14 | NUMA locality | `/sys/class/net/<if>/device/numa_node`, `nvidia-smi topo -m` | NIC *r* PIX to GPU *r* | yes | no |
| 15 | PCIe peer-to-peer allowed | `lspci -vvv` ACSCtl on the switch ports above GPU *r* / NIC *r* | ACS redirect off (or approved IOMMU passthrough) | yes | no |
| 16 | Locked-memory limit | `ulimit -l` in a shell, in `srun bash -c 'ulimit -l'`, in the container | `unlimited` everywhere | yes | no |
| 17 | Per-rail routing and neighbours | `ip rule show`, `ip route show table <rail>`, `ip neigh show dev <if>` | One rule/table per rail; leaf gateway resolved | yes | no |
| 18 | **Switch side** | switch CLI/API or config-compliance tool | 400G up, MTU 9216, trust DSCP, 26 → TC 3 lossless + ECN, 48 → TC 6, PFC prio 3 | yes (read config) | no |
| 19 | Peer validation | `ibv_rc_pingpong -m 4096`, `ib_write_bw -a`, `ib_write_lat -a`, `ib_write_bw --use_cuda=<gpu>` per rail to a known-good peer | Completes; plateau ≥ 95 % of 392 Gb/s; p99 within baseline | **no** (loads the fabric; drained nodes only) | analysis only |
| 20 | Error-counter baseline | `rdma statistic`, `ethtool -S` | Recorded; no transport errors during item 19 | yes | no |

Lab coverage: the lab automates items 1–10 (item 9: DSCP map only) and 12, and correlates item 13 with
perftest results.

## Items host captures cannot verify, and how to get the evidence

- **Switch-port MTU, trust, DSCP→TC, PFC and ECN (item 18):** read the switch configuration through the
  Fabric team's API/CLI, or run a config-compliance tool against intent (Chapter 7 lab, Chapter 20).
- **Whether GPUDirect RDMA actually works:** item 12 only shows that the mechanism exists. Only item
  19's `--use_cuda` run (or NCCL `/GDRDMA` channel lines, Chapter 13) proves it.
- **Cabling to the right leaf port:** LLDP neighbour data (`lldpctl` on the host, or switch LLDP
  tables) compared with the cabling plan.
- **Fabric behaviour under load:** congestion, ECMP collisions, PFC behaviour. Multi-node NCCL tests
  and switch telemetry (Chapter 9).

## Ordering justification

Cheap, read-only, local checks come first (1–17). A failure there makes everything after it
meaningless, and they need no coordination. Switch-side checks (18) come next, because they need the
Fabric team. Peer validation (19) runs **only after configuration is correct and on drained nodes**:
otherwise you benchmark a misconfiguration and may disturb neighbours sharing the rail. The counter
baseline (20) brackets item 19.
