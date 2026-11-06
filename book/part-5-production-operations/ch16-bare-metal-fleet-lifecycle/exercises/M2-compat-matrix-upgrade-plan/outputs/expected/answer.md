# M2 — Compatibility matrix and staged upgrade plan (B-2026.04 → B-2026.10)

## (a) Extended matrix and coupling rules

| Component added | Coupling rule |
|---|---|
| Fabric Manager | Version equals the GPU driver version **exactly**; a mismatch leaves the NVSwitch fabric uninitialized |
| CUDA user-mode | Requires a minimum driver; forward-compatibility packages only within the documented support range, pinned in the bundle |
| DCGM | A major version supports a range of driver branches; pin the version qualified with the bundle's driver |
| NVIDIA container toolkit | Supported against the driver and the container runtime version |
| NVMe firmware | Qualified per drive model (a mixed-model node carries one entry per model) |
| PSU firmware | Qualified per platform; changes power-brake behaviour, so it is tested under burn-in |

## (b) Staged plan for the 32 ORION nodes `[MODELED from ILLUSTRATIVE planning values]`

1. **Qualification:** 2 pilot nodes built *from the production image pipeline* (not hand-built, the
   lesson of Section 16.13), 14 days, full acceptance plus representative W-TRAIN/W-INFER runs.
2. **Canary:** 2 nodes in 2 racks (rack-01, rack-02), 3 h + 72 h bake. Detection of an intermittent
   fault at λ = 0.01 per node-hour: 1 − e^(−0.01 × 2 × 72) = 1 − e^(−1.44) = **76.3 %**. For 95 %:
   λNT ≥ ln 20 ≈ 3.0 → NT ≥ 300 node-hours → 4 nodes × 75 h (or 2 × 150 h).
3. **Waves:** 30 nodes remain; ≤ 4 per wave (12.5 % of capacity); ≤ 1 per rack; largest rack
   remainder 4 → max(⌈30/4⌉, 4) = **8 waves** (7 × 4 + 1 × 2). A wave equals one W-TRAIN DP replica
   (TP 8 × PP 4 = 32 GPUs) *only* if replicas are striped one node per rack; otherwise a wave touches
   up to 4 replicas and must be aligned with checkpoint/restarts instead of claiming DP = 7.
4. **Calendar:** (3 + 72) + 8 × (3 + 12) = 75 + 120 = **195 h ≈ 8.1 days**.
   **Capacity out:** 32 × 3 h = 96 node-hours = **768 GPU-hours**, 96 / (32 × 195) ≈ **1.5 %** of
   campaign capacity.
5. **Maintenance windows:** each wave's 1 h drain starts right after a W-TRAIN checkpoint, so the job
   loses at most the restart time, not work since the last checkpoint.

**Abort conditions (halt, do not just log):** any canary/wave node fails re-acceptance; single-node
NCCL busbw below the bundle baseline *for the same algorithm (NVLS vs Ring)* by more than 3 %
`[ILLUSTRATIVE]`; any new Xid class; RDMA pair bandwidth or link-flap counts worse than the B-2026.04
baseline; job step time on upgraded nodes regressed beyond its run-to-run spread; any operator stop.

| Component | Rollback path |
|---|---|
| OS image, kernel, GPU driver, Fabric Manager, CUDA user-mode, DCGM, container toolkit, RDMA stack | Reimage to previous image ID |
| BIOS, BMC | Dual-bank: activate previous bank, AC cycle, read back |
| NIC firmware, NVMe firmware | Reflash previous version (verify the vendor allows downgrade) |
| GPU VBIOS / NVSwitch / CPLD with anti-rollback (security version) | **Not reversible**: longer qualification, smaller canary, forward-fix only |
| PSU firmware | Vendor tool downgrade if supported; otherwise treat as non-reversible |

**Audit evidence:** change ID (e.g. CHG-7731), per-node before/after Redfish `FirmwareInventory`
read-back, acceptance run IDs and policy version, abort-gate decisions with timestamps and
deciders, approvals, and the drain/enable audit records from the lifecycle service.

`solve.py` derives the canary, wave, calendar, and capacity numbers and asserts the key.
Source: Sections 16.7, 16.8, Figure 16.4.
