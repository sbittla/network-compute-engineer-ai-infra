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

On an **L2 rail VLAN** design, the rail-4 NIC (serving GPU4) now sits in rail 5's VLAN and still reaches
peers: there is no per-link IP adjacency to break. (On ORION's routed /31 plan, the swap would break IP
adjacency and NCCL connections on those NICs would fail outright.) But NCCL's rail-aligned rings assume GPU4
on every node talks through rail 4: traffic from GPU4 on other nodes to GPU4 on n12 now has to leave rail 4 and
cross to rail 5 through the spines (or be forwarded over NVLink by PXN, depending on NCCL version and
configuration). That adds a hop, shares spine capacity with other jobs' traffic and creates congestion
hot-spots, which shows up as lower busbw (≈ 350 → ≈ 300 GB/s) and a larger tail (p99 iteration +40 %).

## Safe fix

Drain `orion-n12` at the next checkpoint; swap the two patch cords per the cabling plan; update and verify
the cabling database; return the node to service only after validation.

## Validation

LLDP shows `orion-be-leaf-r4` / `-r5` on the correct netdevs; mapping-CSV diff against golden is clean;
2-node and 8-node nccl-tests within the fleet floor; the 64-GPU job's p99 iteration time back to baseline over
≥ 5 runs. Add an LLDP-vs-cabling check to the post-maintenance acceptance test.

**Common wrong answers.** Replacing optics despite clean counters; concluding "GDR is fine, so the network is
fine"; fixing by remapping NCCL HCAs in software (hides the fault and breaks rail alignment elsewhere).
