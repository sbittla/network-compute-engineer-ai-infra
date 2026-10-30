# ORION-256 Design Pack — <fill: your name>, <fill: date>

> This is the master document of your Capstone A submission. Every section is required. Replace each
> `<fill: …>` prompt. Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]`, `[ILLUSTRATIVE]` or
> `[VENDOR-SPEC, YYYY-MM]`, and show the formula for every `[MODELED]` value or point to the model
> function that produced it. Link the supporting templates rather than pasting them.

## 0. Executive summary (≤ 200 words)

<fill: the decision you recommend, the two or three numbers that justify it, the top risk and its
mitigation, and what still needs hardware validation.>

## 1. Problem statement

- **Decision to be made:** <fill: e.g., choose the ORION-256 backend fabric and confirm the facility can host it>
- **Workload(s):** <fill: W-TRAIN scenarios considered and why>
- **Constraints:** <fill: budget, facility envelope, schedule, team skills, vendor lead times>
- **Success criteria (testable):** <fill: e.g., step time within x % of the compute-bound bound under the
  launcher's real rank order; every rack within its 2N feed at max load; acceptance plan sized and owned>
- **Out of scope:** <fill>

## 2. Architecture

### 2.1 Cluster overview

<fill: Mermaid diagram of compute, backend fabric, frontend/storage fabric, OOB network, storage,
schedulers, security boundaries and failure domains. Caption it: *Figure A.1 — …*>

### 2.2 Network and host topology

See [topology-worksheet.md](topology-worksheet.md). Summarize here: leaf/spine counts, oversubscription,
rail mapping, addressing and routing plan, QoS for RoCEv2, GPU↔NIC locality.

### 2.3 Bill of materials

See [bom.csv](bom.csv). Summary table by section (compute, backend, frontend, storage, management,
facility, spares) with totals `[ILLUSTRATIVE]` prices.

### 2.4 Data paths

<fill: at least the GPU↔GPU (NVLink, intra-node), GPU↔NIC (PCIe switch, PIX), NIC↔leaf↔spine and
host↔storage paths for one DP all-reduce hop and one checkpoint write, with the bottleneck of each.>

## 3. Assumptions

See [assumptions-register.csv](assumptions-register.csv). List here the five assumptions your
recommendation is most sensitive to, with the sensitivity result for each.

## 4. Implementation and simulation boundary

| Claim in this pack | Evidence class | What would be needed to make it `[MEASURED]` |
|---|---|---|
| <fill> | `[MODELED]` | <fill> |

State plainly which tier you worked at (L1 / L2 / L3) and what the starter-kit model does not capture
(at least: NCCL algorithm and channel selection, real ECMP hashing, PFC/ECN dynamics, thermal
throttling, optics margin, failures during a run).

## 5. Workload and communication model

See [workload-comm-model.md](workload-comm-model.md). Include the scenario × option × layout table.

## 6. Capacity, power and cooling

See [power-cooling-budget.csv](power-cooling-budget.csv) and
[facility-handoff-checklist.md](facility-handoff-checklist.md). Name every rack or row that violates a
constraint, the mitigation, its owner and its lead time.

## 7. Test plan and acceptance plan

See [acceptance-plan.csv](acceptance-plan.csv). Describe the stages (physical → node → rail → cluster
→ workload), the entry and exit criteria for each, and who signs off.

## 8. Results

See [results-table.csv](results-table.csv). Present `[MODELED]` and `[MEASURED]` results in separate
columns or tables; never in the same cell.

## 9. Failure analysis

See [failure-analysis.md](failure-analysis.md).

## 10. Security considerations

<fill: at least: backend fabric isolation from frontend and tenants; BMC/OOB network access control and
credential rotation; firmware supply chain and signed images; switch management-plane AAA; who can
change QoS/PFC configuration; physical security of the hall; data protection for checkpoints and
datasets on the parallel FS.>

## 11. Cost/performance trade-off memo

See [cost-performance-memo.md](cost-performance-memo.md) and the decision record
[adr-fabric-choice.md](adr-fabric-choice.md).

## 12. Final engineering review

See [final-engineering-review.md](final-engineering-review.md): review findings, prioritized next-step
backlog, and the presentation outline.
