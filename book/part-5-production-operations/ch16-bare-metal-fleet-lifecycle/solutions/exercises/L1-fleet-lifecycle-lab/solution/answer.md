# L1 — Fleet lifecycle automation lab (reference results)

Expected checker result: **33/33 checks passed (solution)**. Reference implementation:
`solutions/lab/fleet_lifecycle.py`; full planted-fault list: `solutions/lab/PLANTED_FAULTS.md`.

**Acceptance report (`acceptance_results.json`, 32 nodes): 25 PASS, 1 WARN, 6 FAIL** `[SIMULATED]`

| Node | Verdict | Codes | Raw evidence | Remediation |
|---|---|---|---|---|
| orion-n04 | FAIL | `GPU_COUNT`, `XID_PRESENT` | GPU 5 (BDF `0000:ab:00.0`) absent; Xid 79 on that BDF; DCGM/NCCL "passed" on 7 GPUs | Reseat GPU/baseboard; vendor service if it recurs; full re-acceptance |
| orion-n07 | WARN | `ECC_SBE_ELEVATED` | GPU1 14 corrected errors in 24 h burn-in (warn > 10) | Waiver with expiry; DCGM `-r 4`; monitor the trend |
| orion-n11 | FAIL | `PCIE_DEGRADED` | GPU3 width x8 under load (Gen 5) | Reseat board/riser; inspect connector; re-accept |
| orion-n19 | FAIL | `NIC_SPEED`, `RDMA_PAIR_BW_LOW` | rail-5 NIC 200,000 Mb/s; pair test ≈ 192 Gb/s | One fault, two codes: optic DOM, leaf port config, swap-to-isolate (Chapter 10) |
| orion-n23 | FAIL | `FW_OFF_MATRIX` | NIC7 firmware 28.42.1000 (blocked), other 7 NICs 28.41.1000 | Reflash NIC7 to 28.41.1000; re-accept |
| orion-n27 | FAIL | `THERMAL_THROTTLE` | GPU6 max 89 °C with `SW_THERMAL_SLOWDOWN` | Fans, airflow, heatsink, BMC inlet; rerun burn-in |
| orion-n30 | FAIL | `HBM_ROW_REMAP_PENDING` | GPU2 `row_remap.pending = true`, `dbe_aggregate = 1`, `dbe_volatile = 0` | GPU reset per vendor procedure; confirm not pending; `-r 3`; RMA if it recurs |

Distractors that must *not* fail: orion-n15's Ring NCCL run at ≈ 367 GB/s (Ring floor 330, not the
NVLS floor 400); idle PCIe Gen 1 on ≈ 50 % of GPUs; `SW_POWER_CAP` on ≈ 60 %; 200 Gb/s *frontend*
NICs; small SBE counts.

**Lifecycle replay (36 events): 13 rejected, 23 applied.** Rejected events and codes:
seq 1 n05 `JOBS_STILL_RUNNING`; 8 n14 `TICKET_OPEN`; 10 n21 `ILLEGAL_TRANSITION` (enable from
imaged); 11 n21 `ACCEPTANCE_NOT_PASSED` (WARN without waiver); 14 n26 `INVENTORY_INCOMPLETE`; 18 n29
`FW_OFF_MATRIX`; 23 n12 `ILLEGAL_TRANSITION` (repair from schedulable); 25 n12
`FAULT_DRAIN_REQUIRES_REPAIR`; 27 n12 `MISSING_TICKET`; 29 n14 `SANITIZATION_MISSING`; 31 n14
`ILLEGAL_TRANSITION` (out of retired); 32 n32 `MISSING_REASON`; 33 n40 `UNKNOWN_NODE`.
Final non-schedulable nodes: n03 drained, n05 repair, n12 repair, n14 retired, n26 repair.

**Upgrade planner (target B-2026.10):** 10 excluded (n02, n18 already on target; n05, n09, n14, n21,
n26, n29, n31, n32 not schedulable), 22 eligible; canary of 2 in different racks (reference n01,
n06), remaining 20 → lower bound max(⌈20/4⌉, 3) = 5 waves of 4, ≤ 1 per rack.

**Marking notes.** Deduct in Task 5 if a node's report names a code without the raw value or the
physical cause, or if n19 is described as two independent faults. Ask learners why the plan must be
recomputed before each wave (the replay changes node states).
