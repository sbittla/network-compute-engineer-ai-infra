# 5.10 — Lab 5: topology mapper (reference results)

Graded with the Lab 5 rubric (lab README Section 7, 100 points); the checks listed in `meta.yaml` must PASS
in `solutions/lab/outputs/check_solution.txt`. Reference implementation: `solutions/lab/topo_mapper.py`.
Relies on manuscript Sections 5.6–5.10.

## Mapping

**29 of 32** rows `aligned=True`: all 8 rows of `orion-n01` and of `orion-n02`, 7 of `orion-n17` (GPU3 fails)
and 6 of `orion-n23` (GPU4 and GPU5 fail). `orion-n02` is topologically aligned; its fault is host-level.
The CSV must be keyed by GPU UUID and NIC BDF, with slot, NUMA node and rail (from LLDP).

## Findings per host `[SIMULATED]` capture

| Host | Finding(s) | Raw evidence |
|---|---|---|
| `orion-n01` | none (control) | all GPU rows PIX to their rail NIC; LLDP r0–r7 in order; clean GDR file |
| `orion-n02` | `ACS_REDIRECT` (major), `IOMMU_NOT_PASSTHROUGH` (minor) | `ACSCtl: SrcValid+ … ReqRedir+ CmpltRedir+` on 16 switch ports; `/proc/cmdline` has `intel_iommu=on` without `iommu=pt` |
| `orion-n17` | `NIC_NOT_LOCAL` (GPU3), `NIC_SHARED` (`mlx5_2`) | GPU3 row has no PIX; `NIC4` (`mlx5_3`) is SYS; lstopo `PCI 86:00.0` under Package L#1; `PhySlot: 11`, `NUMANode: 1`; GPU2 and GPU3 both nearest to `mlx5_2` |
| `orion-n23` | `RAIL_MISMATCH` ×2 (blocker), `GDR_PEERMEM_MISSING` (major), `DRIVER_DRIFT` (minor) | LLDP `enp153s0np0 → orion-be-leaf-r5`, `enp163s0np0 → orion-be-leaf-r4`; empty lsmod section; driver `550.127.05` |

## Scenarios `[MODELED]` (16-node job, Table 5.4 parameters)

| Scenario | Median (ms) | p99 (ms) | busbw (GB/s) | CV |
|---|---|---|---|---|
| S1 aligned, 16 healthy | 6.05 | 6.17 | 352.3 | 0.008 |
| S2 cross-socket, 16 healthy (SYS → host-staged by the gate) | 52.25 | 74.18 | 40.8 | 0.269 |
| S3 14 healthy + n02 + n17, nearest | 12.07 | 12.85 | 176.6 | 0.027 |
| S4 same nodes, forced aligned | 15.33 | 37.45 | 139.0 | 0.331 |
| S5 same nodes, PXN (falls back to nearest on n17) | 12.07 | 12.85 | 176.6 | 0.027 |
| S4@SYS (`NCCL_NET_GDR_LEVEL=SYS`) | 11.46 | 18.32 | 186.0 | 0.173 |

Reasoning to look for: with the default GDR gate (≈ PXB), forcing alignment on n17 is *worse* than nearest
(it reverses if the host-staged rate exceeds 22.5 GB/s); PXN never engages on n17 because no peer GPU reaches
the misplaced NIC at ≤ PXB (best is PHB from GPU4/5), so S5 = S3; S2's deterministic value is 15.0 ms /
≈ 142 GB/s, the 52 ms median being an independent-CV sensitivity case; fixing n17 alone leaves n02 capping the
job at ≈ 262 GB/s. n23 (blocker) must not be scheduled at all.

## Report (Task 6, 30 points)

Diagram (6), recommendations with drain/fix/policy reasoning (6): drain n23 and fix cables + load
`nvidia_peermem` or verify DMA-BUF; schedule n02 only after restoring the BIOS baseline (ACS off,
`iommu=pt`); move n17's NIC to slot 4; validation checklist with pass criteria (6); L3 methodology with
repetitions and manifest (6); limitations and correct labels (6).

**Common mistakes.** Keying by GPU index; treating `NICk` as `mlx5_k`; flagging n23 GPU4/5 as `NIC_NOT_LOCAL`
(they have a PIX NIC, cabled wrong); running the model with n23 included; presenting Table 5.5 as measured.
