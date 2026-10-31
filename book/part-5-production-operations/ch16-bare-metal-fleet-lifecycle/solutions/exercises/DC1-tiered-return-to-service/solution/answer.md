# DC1 — Tiered return-to-service policy

**Invariant kept.** Every repaired node still re-enters at `imaged` and reaches `schedulable` only
through `validated`; the tier only selects *how deep* the acceptance run is, from the repair
ticket's replaced-part list (which the reconciler cross-checks against the inventory diff).

| Repair type (share) | Tier | Tests | Duration `[ILLUSTRATIVE]` |
|---|---|---|---|
| All | Base | Inventory diff, firmware matrix, DCGM `-r 1`, single-node NCCL | 20 min (included in every tier) |
| Optic / cable (60 %) | Link | Base + NIC link/speed, optic DOM, RDMA pair test on the affected rail, 15 min traffic soak watching FEC/symbol errors | 0.75 h |
| NIC (25 %) | NIC | Base + per-device NIC firmware, all rails link + RDMA pairs, 2 h network soak | 2.5 h |
| GPU / baseboard (10 %) | Full | Full acceptance including 24 h burn-in (Figure 16.3) | 25.4 h |
| DIMM / NVMe (5 %) | Host | Base + memory test, SMART + `fio`, DCGM `-r 2`, 4 h burn | 5 h |

**Weighted average** `[MODELED]`:
0.60 × 0.75 + 0.25 × 2.5 + 0.10 × 25.4 + 0.05 × 5
= 0.45 + 0.625 + 2.54 + 0.25 = **3.87 h** per repair, versus **25.4 h** for full acceptance
(1 − 3.87 / 25.4 ≈ **85 %** less re-acceptance time). Note that the 10 % GPU/baseboard repairs
contribute 2.54 of the 3.87 h: the policy's savings come entirely from not burning in link repairs.

**Residual risk: collateral damage outside the tested tier.** A technician swapping an optic or a
NIC can unseat an adjacent GPU or cable, or leave an airflow baffle out; a Link-tier run does not
burn in or check thermals. Mitigations: the Base tier always runs DCGM `-r 1` and single-node NCCL
(catches unseated GPUs and many NVLink faults). *Detection in production:* for the first 24 h after
return, flag any repaired node that shows thermal slowdown reasons, a new Xid, or single-node /
job-peer NCCL busbw more than 3 % below its own baseline, and automatically demote it to full
acceptance `[ILLUSTRATIVE threshold]`. A second residual risk worth naming: an intermittent GPU
fault misattributed to a cable; a repeat repair on the same slot within 30 days should force the
Full tier.

**Common mistakes:** adding a `repair → schedulable` shortcut; weighting durations without the base
tier; no threshold on the detection signal. Source: Sections 16.5, 16.6 (25.4 h per node), 16.9.
