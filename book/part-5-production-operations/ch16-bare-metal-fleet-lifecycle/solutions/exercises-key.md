# Chapter 16 — Exercise Answer Key (INSTRUCTOR ONLY)

Marking scale per exercise is given in brackets. "Common mistakes" lists what to deduct for. All
arithmetic was checked twice (by hand and with a Python one-liner); results are rounded only at the
final step.

---

## A. Knowledge checks (5 points each)

**K1.** discovered → imaged → validated → schedulable → draining → drained → repair → retired.
Only `validated` (event `enable`) and `draining` (event `cancel_drain`, maintenance drains only) lead
to `schedulable`. There is no `repair → schedulable` edge because a repaired node has changed
hardware or firmware and is unproven; it must re-enter at `imaged` and pass acceptance. [2 states
list, 2 sources, 1 justification.]
*Common mistakes:* listing `imaged → schedulable`; forgetting the maintenance-only cancel path.

**K2.** Not a defect. GPUs lower PCIe link *speed* when idle to save power and return to Gen 5 under
load. It would be a defect if (a) the link stayed below Gen 5 *under load*, or (b) the *width* dropped
below x16 (width does not change with load; x8 indicates a lane, seating, or signal-integrity
problem and halves bandwidth to ≈ 31.5 GB/s per direction). [3 verdict + mechanism, 2 defect
condition.]

**K3.** Pending remap: the driver has recorded a failing HBM row to remap to a spare, but the remap
takes effect only after a GPU reset; until then the GPU should not run production. Action: drain,
reset per vendor procedure, confirm `Pending: No`, re-run DCGM `-r 3`. Remapping failure: the GPU
could not remap (spares exhausted or the operation failed) — the GPU is an RMA candidate; drain and
open RMA with `nvidia-bug-report.sh` and DCGM output. [2 + 2 + 1.]

**K4.** `SW Thermal Slowdown` on GPU 6 fails acceptance (the policy fails HW/SW thermal slowdown and
HW power brake). `SW Power Cap` is normal under full load: the GPU is at its 700 W limit. Causes for
GPU 6: blocked or failed fan / airflow obstruction in that slot, missing blanking panel or rack
recirculation, poor heatsink contact (thermal interface), or high inlet temperature. [2 + 1 + 2.]

**K5.** With *c* components each having *v* candidate versions, pairwise tables need
C(c,2)·v² entries and still say nothing about combinations of three or more; bundles qualify a small
number of complete combinations as units. Example three-way interaction: GPU driver + fabric manager
+ NVSwitch firmware (the fabric initialises only when all three agree), or NIC firmware + RDMA stack +
GPU driver for GPUDirect RDMA (`nvidia-peermem`/DMA-BUF). [3 + 2.]

**K6.** (a) PATCH `/redfish/v1/Systems/{id}` with `Boot.BootSourceOverrideTarget = Pxe`,
`BootSourceOverrideEnabled = Once`; (b) POST
`/redfish/v1/Systems/{id}/Actions/ComputerSystem.Reset` with a `ResetType`; (c) GET
`/redfish/v1/UpdateService/FirmwareInventory`. Many firmware images are *staged* and activate only
after reboot/AC cycle; the update task can report completion while the old image still runs, so the
running version must be read back before declaring success. [1 + 1 + 1 + 2.]

**K7.** Purge. Overwriting the file system does not reach over-provisioned space, remapped/retired
blocks, or data outside the file system; Sanitize crypto erase destroys the media encryption key (or
block erase resets all NAND), covering the whole device. Record a certificate: device serials,
method, tool/version, operator, date, verification result. [1 + 2 + 2.]

---

## B. Worked problems (15 points each)

**W1.**
(a) Remaining after canary: 512 − 4 = 508 nodes. Per-rack constraint: largest rack remainder = 4
(racks without a canary node), so ≥ 4 waves. Per-wave cap: ⌈508 / 32⌉ = ⌈15.875⌉ = 16 waves.
Waves = max(16, 4) = **16** (15 × 32 + 1 × 28). Feasibility: 32 nodes per wave needs 32 distinct
racks; 128 racks are available.
(b) Calendar = canary (3 h + 72 h) + 16 × (3 h + 6 h) = 75 + 144 = **219 h ≈ 9.1 days**.
(c) Every node is out once for 3 h: 512 × 3 = **1,536 node-hours = 12,288 GPU-hours** (× 8).
(d) N T = 4 × 72 = 288 node-hours.
λ = 0.01: P = 1 − e^(−2.88) = 1 − 0.0561 = **94.4 %**.
λ = 0.001: P = 1 − e^(−0.288) = 1 − 0.750 = **25.0 %**.
(e) Need e^(−λNT) ≤ 0.10 → λNT ≥ ln 10 = 2.303 → NT ≥ **2,303 node-hours** (e.g., 32 nodes × 72 h
= 2,304). Conclusion: canaries cost-effectively catch *common* regressions; rare faults (once per
thousands of node-hours) can only be caught by fleet-wide telemetry comparing upgraded vs
non-upgraded cohorts during and after the campaign, plus a fast rollback path.
[a 3, b 3, c 2, d 4, e 3.] *Common mistakes:* forgetting the canary nodes in (c); using 512 instead
of 508 in (a); confusing node-hours with GPU-hours.

**W2.**
(a) T = 0.7 × 17.4 / 0.85 + 0.3 × 17.4 = 14.33 + 5.22 = **19.55 s**. Loss = 1 − 17.4 / 19.55 =
**11.0 %**. GPU-equivalents = 256 × 0.110 = **28.1 GPUs**.
(b) Gen5 x16 = 32 GT/s × 16 × 128/130 / 8 = 63.0 GB/s per direction; x8 = **31.5 GB/s**, which is
below the NIC's 50 GB/s line rate, so PCIe becomes the bottleneck. At 85 %: 26.8 GB/s.
Time = 7.66 / 26.8 = 0.286 s versus 0.170 s healthy → **+0.116 s per step = 0.67 %** of 17.4 s (if
fully exposed).
(c) The throttling GPU is ≈ 16× worse for *this* job because it sits on the compute critical path of
every step; the NIC costs < 1 % because the DP all-reduce is small relative to the step and can
overlap. Acceptance must still reject both: other jobs (expert-parallel all-to-all, larger DP,
inference KV transfer, checkpoint staging through the same PCIe switch) put the NIC on their
critical path, and acceptance cannot know which job will land on the node.
[a 6, b 6, c 3.] *Common mistakes:* applying 0.85 to the whole step; using 400 Gb/s instead of the
PCIe ceiling in (b); treating 31.5 GB/s as bidirectional.

---

## C. Hands-on lab (graded by the lab rubric in lab/README.md; 100 points)

Expected `check.py` result: 33/33 PASS. Expected acceptance report and lifecycle outcomes: see
[lab/PLANTED_FAULTS.md](lab/PLANTED_FAULTS.md).

---

## D. Troubleshooting case T1 (20 points)

1. **Decode.** `0x24 = 0x20 | 0x04` → SW Thermal Slowdown + SW Power Cap. `0x4` alone (night) is
   normal power capping. [3]
2. **Hypotheses ranked:**
   H1 *Rack-level airflow/cooling problem in rack-04* — all four rack-04 nodes show inlet 31–32 °C at
   15:00 versus 24–25 °C in neighbouring racks; FAC-2210 removed a containment panel two weeks ago;
   time-of-day pattern matches facility load/outdoor temperature.
   H2 *Node-level fan/heatsink fault on orion-n14* — would not explain rack-wide inlet rise or the
   night-time recovery.
   H3 *Workload change (hotter kernels in the afternoon)* — the same job on other racks is fine.
   [5: correct ranking with reasons.]
3. **Discriminating tests:** H1 — log inlet temperature for all rack-04 nodes and the cold-aisle
   sensor across 24 h; inspect containment; compare with rack-03/r5. H2 — fan RPM and per-GPU
   temperature deltas versus rack peers at the same inlet temperature. H3 — run the same job on
   rack-03 nodes in the afternoon. [4]
4. **Root cause:** missing cold-aisle containment panel lets hot exhaust recirculate into rack-04's
   inlet; in the afternoon the margin disappears, GPUs reach their software thermal limit, and the
   synchronous job runs at the pace of the slowest GPU. **Safe change:** Facilities reinstalls the
   panel (non-disruptive to IT load), under a facilities change ticket. **Validation:** for 3
   consecutive days, rack-04 inlet ≤ 27 °C at 15:00 (the ASHRAE-recommended upper bound for most
   IT equipment classes; verify against your facility's design), no `0x20`/`0x40` reasons on
   rack-04 GPUs, and job step-time p99/p50 back within the normal spread (e.g., ≤ 3 %). [5]
5. **Lifecycle:** do *not* fault-drain or send the nodes to repair — the hardware is healthy. Until
   validated, steer large synchronous jobs away from rack-04 using scheduler constraints (Chapter 17)
   or a maintenance drain with a reason referencing FAC-2210; record the event against the rack, not
   the nodes. [3]
*Common mistakes:* RMA-ing GPUs; treating `SW Power Cap` as the fault; no validation threshold.

---

## E. Design challenge DC1 (20 points)

Reference policy (all tiers keep the "re-enter at `imaged`, pass to `validated`" rule):

| Repair type | Tier | Tests | Duration [ILLUSTRATIVE] |
|---|---|---|---|
| All | Base | Inventory diff, firmware matrix, DCGM `-r 1`, single-node NCCL | 20 min (included below) |
| Optic / cable | Link | Base + NIC link/speed, optic DOM, RDMA pair test on the affected rail, 15 min traffic soak watching FEC/symbol errors | 0.75 h |
| NIC | NIC | Base + NIC firmware per device, all rails link + RDMA pairs, 2 h network soak | 2.5 h |
| GPU / baseboard | Full | Full acceptance incl. 24 h burn-in | 25.4 h |
| DIMM / NVMe | Host | Base + memory test, storage SMART + fio, DCGM `-r 2`, 4 h burn | 5 h |

Weighted average = 0.60 × 0.75 + 0.25 × 2.5 + 0.10 × 25.4 + 0.05 × 5
= 0.45 + 0.625 + 2.54 + 0.25 = **3.87 h** versus 25.4 h for full acceptance (≈ 85 % less).

Residual risk: collateral damage during the repair (a technician unseats an adjacent GPU or cable,
or leaves an airflow baffle out) that the narrow tier does not test. Mitigations and detection: the
base tier always runs single-node NCCL and DCGM `-r 1` (catches unseated GPUs and many NVLink
faults); in production, flag any repaired node whose first 24 h shows thermal slowdown reasons, new
Xids, or NCCL busbw below the node baseline by > 3 %, and automatically demote it to full acceptance.
[Table 8, arithmetic 6, risk + signal + threshold 6.]

---

## F. Outline-mandated exercises

**M1 (20 points).** Reference answer is Table 16.4 plus Figure 16.3 ordering. A full-mark answer
has ≥ 12 checks in fail-fast order: inventory diff → firmware matrix → PCIe topology/width →
GPU discovery/HBM → ECC and row remap (DCGM `-r 1`) → NVLink/fabric state → NIC link, speed, MTU →
RDMA pair tests per rail → storage SMART + fio → DCGM `-r 3` → burn-in (12–48 h, thermals and
throttle reasons logged) → single-node NCCL. Each with tool, measure, threshold labelled
ILLUSTRATIVE or derived from a measured baseline, FAIL/WARN class (WARN: SBE counts, deprecated
bundle), duration, and a total (≈ 25 h with 24 h burn-in). Must record policy version and raw
outputs. [Coverage 8, ordering 4, thresholds and classes 5, duration/policy version 3.]
*Common mistakes:* RDMA host-loopback instead of same-rail pair tests; judging PCIe speed at idle;
no single-node NCCL; no WARN class.

**M2 (25 points).** (a) Extended matrix couplings: fabric manager = driver version exactly; CUDA
user-mode requires minimum driver (forward-compat package only within documented support); DCGM
major version supports a range of driver branches; NVIDIA container toolkit version supports the
driver and container runtime; NVMe firmware qualified per drive model; PSU firmware per platform
(power-brake behaviour). (b) Plan, reference numbers from Section 16.8: qualification on 2 pilot
nodes built *from the production image pipeline* (lesson of Section 16.13); canary 2 nodes in 2
racks, 72 h bake → 76 % detection at λ = 0.01/node-hour (or 4 nodes × 75 h for 95 %); waves of 4, ≤ 1 per rack → 8 waves (a wave equals one DP replica *only* if
replicas are striped one node per rack; full marks require stating this condition or dropping the
DP = 7 claim); 195 h ≈ 8.1 days; 768 GPU-hours out; waves aligned to
W-TRAIN checkpoints; abort conditions: any re-acceptance failure, single-node NCCL busbw < the bundle's baseline *for the same NCCL algorithm (NVLS vs Ring)* − 3 %, new
Xid class, RDMA/link-flap regression, step-time regression on upgraded nodes, operator stop.
Rollback table must mark at least one component non-reversible (anti-rollback firmware) and give
dual-bank and reimage paths for the others. Audit evidence: change ID, per-node before/after
firmware inventory (Redfish FirmwareInventory read-back), acceptance run IDs, abort-gate decisions
with timestamps, approvals. [Matrix 6, numbers derived 8, abort 4, rollback 4, evidence 3.]
Accept other wave sizes if derived and justified against blast radius and the training job.

**M3 (15 points).** Reference: Figure 16.1 and `solutions/lab/fleet_lifecycle.py`
`transition_table()` (13 transitions) and guards. Forbidden transitions with reasons:
`repair/imaged → schedulable` (unvalidated hardware), `schedulable → repair` (must drain; running
jobs), `draining → schedulable` for fault drains (fault not resolved), any transition out of
`retired` (terminal; asset sanitized), `discovered → validated` (no image/acceptance). Audit fields:
seq, ts, node, event, actor, from_state, to_state, result, reason_code (+ change/ticket IDs).
[Diagram 3, transition table 5, forbidden table 4, lab checks 3.]

---

## G. Reflection (5 points each; full marks for a specific, evidence-aware answer)

**R1.** Run acceptance on ≥ 20 known-good nodes (or all, excluding failures), ≥ 5 repetitions per
metric per node after warm-up; compute the per-metric population median and spread (IQR or p5);
set FAIL at a margin below the population's low tail (e.g., median − 3 × robust spread, or p1),
WARN between; re-baseline per bundle. State that thresholds are MEASURED for that environment.

**R2.** Examples: a bad manufacturing batch of optics/GPUs (failures cluster by lot → canary should
sample lots; track lot in inventory); rack-level power/cooling events (cluster by rack → per-rack wave
caps); firmware bugs triggered by a specific workload (cluster by job → bake on representative
workloads); shared PDU/upstream switch.

**R3.** Missing: multi-node fabric behaviour (switch-side counters, ECN/PFC behaviour under load,
cross-rail routing, ECMP polarisation), multi-node NCCL at scale, long-tail intermittent faults,
interaction with other tenants' traffic. Covered by Chapters 9, 10, 12, 13 (multi-node NCCL and
fabric validation) and Chapter 18 (production telemetry).

**R4.** A reasonable answer: do not waive silently. Either reflash to the bundle (fast, proven) or
fast-track a candidate bundle containing the new NIC firmware through qualification (pilot nodes,
canary, bake) with explicit approval; a time-limited waiver is acceptable only with a documented
risk owner, monitoring for the specific bug, and an expiry. Evidence: vendor release notes for the
fix, your own reproduction of the bug and the fix on a pilot, acceptance results, approval record.

---

## H. Deliverable D1 (graded with this rubric, 100 points)

| Criterion | Points |
|---|---|
| Acceptance spec complete, fail-fast ordered, thresholds labelled and justified | 25 |
| Evaluator schema and reason-code catalogue consistent with lab | 10 |
| State machine with guards, forbidden transitions, audit schema | 15 |
| Compatibility matrix process and staged upgrade with derived numbers | 20 |
| Runbook: signals, thresholds, safe actions, evidence capture, escalation | 20 |
| Realism section and evidence appendix (lab report, check output, manifest if L2/L3) | 10 |
