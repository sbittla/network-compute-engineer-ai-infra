# 5.16 — One node slow after a rack move (model answer)

Relies on manuscript Section 5.8 (multi-rail), Section 5.12 (troubleshooting scenario) and
docs/REFERENCE_CLUSTER.md (backend rails). Case facts `[ILLUSTRATIVE]`.

## Ranked hypotheses and tests

| Rank | Hypothesis | Test | Result in the case |
|---|---|---|---|
| 1 | Swapped cables on `orion-n12` rails 4/5 during re-cabling | LLDP per netdev vs the cabling database | **Confirmed**: `enp153s0np0` (rail-4 NIC) sees `orion-be-leaf-r5`, `enp163s0np0` sees `-r4` |
| 2 | Optics/FEC errors on the moved links | Leaf interface counters, FEC corrected/uncorrected | Ruled out: counters clean |
| 3 | GPUDirect RDMA disabled after the move | NCCL channel lines | Ruled out: `/GDRDMA` on all NICs |
| 4 | PCIe link degradation (reseated cards) | `lspci -vvv` `LnkSta` speed/width | Clean in the case; `topo -m` golden |

**Root cause:** a patch-panel swap of the rail-4 and rail-5 cords during the rack move.

## Why the job still runs, but slower

In this pod all backend NICs share **one stretched L2 domain**: one VLAN and IP subnet spanning every rail
leaf, stretched over the spines with EVPN-VXLAN. The rail-4 NIC (`mlx5_4`, serving GPU4) is now plugged into `orion-be-leaf-r5`, yet it
still reaches every peer: the switches learn its MAC on the new port and there is no per-link IP adjacency to
break. (On ORION's routed /31 plan the swap would break IP adjacency and NCCL connections on those NICs would
fail outright.)

NCCL cannot see a cabling error. The PCIe topology is unchanged, so it still pairs GPU4 with `mlx5_4` and
builds rail-aligned rings. Traffic from GPU4 on the other nodes leaves on their rail-4 NICs into
`orion-be-leaf-r4` and must now cross a spine to reach n12's `mlx5_4` on `orion-be-leaf-r5`; rail-5 traffic to
n12's GPU5 crosses the spines the other way. Both rails' flows to n12 take an extra hop and share spine links
with other traffic; the VXLAN underlay spreads them by ECMP hashing, and collisions create hot spots.
(If the domain were stretched with STP/MLAG instead, there would be no per-flow hashing: blocked or pinned
spine paths would concentrate both rails' flows onto fewer links, with the same symptom.) That shows up as lower busbw (≈ 350 → ≈ 300 GB/s)
and a larger tail (p99 iteration +40 %).

## Safe fix

Drain `orion-n12` at the next checkpoint; swap the two patch cords per the cabling plan; update and verify
the cabling database; return the node to service only after validation.

## Validation

LLDP shows `orion-be-leaf-r4` / `-r5` on the correct netdevs; mapping-CSV diff against golden is clean;
2-node and 8-node nccl-tests within the fleet floor; the 64-GPU job's p99 iteration time back to baseline over
≥ 5 runs. Add an LLDP-vs-cabling check to the post-maintenance acceptance test.

**Common wrong answers.** Replacing optics despite clean counters; concluding "GDR is fine, so the network is
fine"; fixing by remapping NCCL HCAs in software (hides the fault and breaks rail alignment elsewhere).
