# Runbook Excerpts — ORION-256 (Capstone A)

> **Safety:** Production actions follow change control. Read-only steps come first. Every disruptive
> step names its approver. The two procedures below are required. Add more for your design.

## RB-1a: Rail-leaf failure (option A, rail-optimized)

**Signal:** BGP sessions to `orion-be-leaf-r<R>` down on all spines; all 32 host links on rail R down; NCCL
timeouts or a step-time collapse on W-TRAIN. **Every node loses one of its eight rails. No node is lost,**
so shrinking DP removes nothing.

| Step | Action (read-only first) | Owner | Approval |
|---|---|---|---|
| 1 | Confirm scope: spine BGP neighbour state, leaf reachability via OOB console, `rdma link` / `ip link` for `mlx5_<R>` on two nodes | Fabric on-call | none |
| 2 | Check whether the job is progressing (step-time metric, NCCL watchdog logs) | Training Infra on-call | none |
| 3 | Choose one: **(i)** wait for repair (spare leaf on site?) if the repair ETA × lost throughput < restart cost (≈ 900 s); **(ii)** checkpoint and restart on 7 rails by excluding the failed HCA (e.g. `NCCL_IB_HCA=^mlx5_<R>` `[VENDOR-SPEC, 2026-10]`, verify the exclusion syntax for your NCCL version): ≈ 12.5 % less inter-node bandwidth, and GPU R's traffic must leave through another rail's NIC via PXN/NVLink, which can make rings cross-rail through the spines; validate with a short `all_reduce_perf` before resuming; **(iii)** take the job down until repair. <fill: decision and rationale> | Training Infra lead | Fabric lead |
| 4 | <fill: leaf replacement / RMA; post-repair acceptance: link DDM (`ethtool -m`), BGP up, per-rail `ib_write_bw` on ring neighbours> | Fabric | Change advisory |
| 5 | Restore all 8 rails (remove the HCA exclusion) at the next checkpoint boundary; confirm step time back at baseline | Training Infra | Fabric |

## RB-1b: ToR-leaf failure (option B, top-of-rack)

**Signal:** all 8 rails of the 4 nodes in one rack down. One TP8 × PP4 replica (4 nodes, 32 GPUs) is lost.

| Step | Action (read-only first) | Owner | Approval |
|---|---|---|---|
| 1 | Confirm scope as in RB-1a, step 1 | Fabric on-call | none |
| 2 | Drain the 4 nodes in Slurm (`scontrol update nodename=... state=drain reason=...`); draining stops new placement but does not move the running job | Platform | Training Infra lead |
| 3 | <fill: wait for repair, or checkpoint and restart at DP = 7 (224 GPUs, −12.5 %), which needs a global batch divisible by 7 or a batch/LR change. There are no spare nodes. Compare against the ≈ 900 s restart cost> | Training Infra lead | Platform |
| 4 | <fill: replacement and acceptance as in RB-1a, step 4> | Fabric | Change advisory |
| 5 | Return the nodes to service only after acceptance passes; restart at DP = 8 at the next checkpoint | Fleet | Fabric |

**Escalation (both):** <fill>. **Validation:** <fill: step time back within x % of baseline for 30 min>.

## RB-2: Power-cap event on rack-05 (63 A feeds)

**Signal:** PDU per-phase current above the 80 % continuous limit on either feed, a single-feed alarm, or
node power above the rack-05 cap.

| Step | Action | Owner | Approval |
|---|---|---|---|
| 1 | Read PDU telemetry for both feeds; confirm whether one feed is lost (2N exposure) | Facilities | none |
| 2 | Read node power (`nvidia-smi -q -d POWER`, BMC chassis power) on rack-05 nodes | Fleet | none |
| 3 | <fill: if a feed is lost and load > 34.42 kW, apply the pre-approved GPU power cap (≈ 500 W/GPU) via the change-controlled automation, or drain rack-05 nodes; note that capped nodes become stragglers for synchronous jobs> | Fleet | Facilities + Training Infra |
| 4 | <fill: restore feed; remove cap; verify> | Facilities | Change advisory |

**Escalation:** <fill>. **Post-incident:** <fill: confirm re-feed to 80 A is scheduled>.
