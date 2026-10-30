# Capstone A: Design a 256-GPU AI Training Cluster

You will produce the design pack that Halcyon AI needs before it orders ORION-256: an architecture
and bill of materials, network and host topology, a workload and communication model for W-TRAIN,
capacity and power assumptions checked against the real facility envelope, an acceptance plan, a
failure analysis, and a cost/performance memo that recommends a backend fabric and defends it with
numbers. This is the work a cluster architect does in the eight weeks before a purchase order. It is
also where most expensive mistakes are made. Racks that cannot be powered with 2N redundancy, optics
that do not reach, and fabrics whose oversubscription only shows up under the scheduler's real rank
order are all cheaper to find in a spreadsheet than on the data-centre floor.

## Audience and prerequisites

**Audience (course outline, Section 16):** AI infrastructure architect, cluster engineer, network engineer.

**Recommended preparation:** Chapters [2](../../book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/),
[5](../../book/part-2-accelerated-compute/ch05-gpu-interconnects-host-topology/),
[7](../../book/part-3-networking/ch07-ethernet-datacenter-network-foundations/),
[8](../../book/part-3-networking/ch08-rdma-rocev2-infiniband/),
[10](../../book/part-3-networking/ch10-switches-optics-physical-layer/),
[11](../../book/part-4-distributed-ai/ch11-distributed-training-architecture/),
[12](../../book/part-4-distributed-ai/ch12-collective-communication-nccl/) and
[21](../../book/part-5-production-operations/ch21-capacity-power-economics/). Chapters
[16](../../book/part-5-production-operations/ch16-bare-metal-fleet-lifecycle/) and
[19](../../book/part-5-production-operations/ch19-reliability-security-multitenancy/) feed the acceptance
plan and the failure analysis.

## Scenario

Halcyon AI has been allocated 13 racks in a hall (positions in rows A, B and D) and wants to train a 70-billion-parameter
dense model (W-TRAIN, [REFERENCE_CLUSTER.md](../../docs/REFERENCE_CLUSTER.md) §3) on 32 HX8 nodes, which
is 256 H100-class GPUs. Each node has eight 400 Gb/s RDMA NICs, one per GPU and one per rail. Three
backend proposals are on the table.

| Option | Shape | Who proposed it |
|---|---|---|
| A | Rail-optimized leaf-spine: one 64-port leaf per rail, 32 down / 32 up, 4 spines, 1:1 | Fabric team (this is the ORION baseline) |
| B | Top-of-rack leaf per GPU rack carrying all 8 rails of 4 nodes, 32 down / 16 up, 2 spines, 2:1 | Finance asked for a cheaper option |
| C | 48 down / 16 up per leaf, 6 leaves | A vendor's quote, cheapest on paper |

Facilities has sent the hall drawing and the feed schedule. One GPU position has older 63 A feeds,
and the eighth GPU rack sits in an overflow position at the far end of the hall, in a legacy
air-cooled row. Training Infra will launch W-TRAIN as either the 3D-parallel baseline (TP = 8, PP = 4,
DP = 8) or a fully sharded variant (TP = 8, DP = 32). The launcher takes its node order from the
inventory API, which does not sort by rack. By default ORION splits its 32 nodes into 24 training
(`orion-n01`–`n24`) and 8 inference (`orion-n25`–`n32`) nodes. A full-size W-TRAIN run borrows the
inference nodes through a lifecycle transition, and there are **no spare nodes** outside the 32
([REFERENCE_CLUSTER.md](../../docs/REFERENCE_CLUSTER.md) §2). Any spare pool you propose is a declared
variation that must be priced in the BOM.

## Problem statement

Recommend a backend fabric for ORION-256 and show that the facility can host it. Your recommendation
must be supported by a reproducible model and must state, for every number, whether it is measured,
modeled or illustrative. Success means:

1. Every rack meets its 2N feed limit and every row meets N+1 cooling at maximum load, or you name the
   violation, the mitigation, the owner and the residual risk.
2. The communication model shows how each fabric option behaves under the launcher's actual rank order,
   not only under an ideal one.
3. The cost/performance memo states a break-even condition and what evidence would change the decision.
4. The acceptance plan is sized from your cable plan and is executable by the Fleet and Fabric teams.

## Required artifacts

The first seven rows are the Capstone A artifacts from the course outline (Section 16). The remaining
rows are required of every capstone.

| Artifact | Template | Expected evidence label |
|---|---|---|
| Architecture and bill of materials | [design-pack.md](templates/design-pack.md) §2, [bom.csv](templates/bom.csv) | `[MODELED]` from `[ILLUSTRATIVE]` prices |
| Network and host topology | [topology-worksheet.md](templates/topology-worksheet.md) | `[MODELED]`; `[MEASURED]` topology dumps if L2 |
| Workload/communication model | [workload-comm-model.md](templates/workload-comm-model.md) | `[MODELED]` |
| Capacity and power assumptions | [power-cooling-budget.csv](templates/power-cooling-budget.csv), [facility-handoff-checklist.md](templates/facility-handoff-checklist.md), [assumptions-register.csv](templates/assumptions-register.csv) | `[MODELED]`, `[ILLUSTRATIVE]` |
| Acceptance plan | [acceptance-plan.csv](templates/acceptance-plan.csv) | procedure + pass criteria |
| Failure analysis | [failure-analysis.md](templates/failure-analysis.md), [runbook.md](templates/runbook.md) (rail-leaf failure, rack-05 power-cap event) | `[MODELED]` / qualitative |
| Cost/performance trade-off memo | [cost-performance-memo.md](templates/cost-performance-memo.md), [adr-fabric-choice.md](templates/adr-fabric-choice.md) | `[MODELED]` |
| Problem statement; architecture; assumptions | [design-pack.md](templates/design-pack.md) §1–3 | |
| Implementation or simulation boundary | [design-pack.md](templates/design-pack.md) §4 | |
| Test plan; results | [acceptance-plan.csv](templates/acceptance-plan.csv), [results-table.csv](templates/results-table.csv) | `[MODELED]` and `[MEASURED]` kept apart |
| Failure analysis; security considerations | [failure-analysis.md](templates/failure-analysis.md), [design-pack.md](templates/design-pack.md) §10 | |
| Final engineering review | [final-engineering-review.md](templates/final-engineering-review.md) | |

## Milestones

| Milestone | Week | What you hand in |
|---|---|---|
| M0: choose | 8 | Capstone choice; read the scenario and the dataset |
| M1: proposal | 10 | Problem statement, assumptions register v1, architecture sketch, and checks 01–07 passing |
| M2: model | 12 | All 16 checks passing; topology worksheet, power/cooling budget, workload model |
| M3: draft | 13 | BOM, acceptance plan, failure analysis, memo draft, sensitivity analysis; peer review booked |
| M4: final | 14 | Complete design pack, final engineering review, 15-minute presentation |

## Tier options

| Tier | Scope | What it adds to your grade |
|---|---|---|
| **L1 (required)** | [starter-kit](starter-kit/): implement the model, use it to fill the templates | Full marks are achievable at L1 if every number is correctly labelled |
| **L2 (optional)** | One HX8-class host: topology dumps, GPU↔NIC locality, sustained chassis power | Replaces node-power and topology assumptions with `[MEASURED]` values |
| **L3 (optional)** | Two or more nodes on a rail-optimized fabric: per-rail perftest, `all_reduce_perf` under two rank orders, optic DDM | `[MEASURED]` evidence for the oversubscription comparison |

**Advanced extension (course outline):** compare two fabric or topology options and quantify the expected
oversubscription and its communication consequences. Starter-kit tasks 6 and 7 cover this at L1.
Physical claims require a real, compatible lab: the procedure is in the
[starter-kit README, Section 8](starter-kit/README.md#8-extensions-hardware-backed-validation-l2l3).

> **Realism boundary:** The starter-kit model is a planning model. It assumes perfect ECMP and treats
> each flow as wanting the full NIC rate. It ignores NCCL's algorithm and channel selection, PFC/ECN
> dynamics, thermal throttling and failures during a run. Prices, power figures and the facility are
> `[ILLUSTRATIVE]`. A design pack that presents any of its outputs as a measurement fails the
> measurement dimension.

## How the chapters map to the artifacts

| Artifact | Chapters |
|---|---|
| Architecture, BOM | 1, 2, 21 |
| Network topology, cable plan, optics | 7, 8, 10 |
| Host topology, GPU↔NIC locality | 3, 5, 13 |
| Workload/communication model | 11, 12, 13, 22 |
| Capacity, power, cooling | 2, 21 |
| Acceptance plan | 10, 16, 12 |
| Failure analysis, security | 18, 19, 20 |
| Memo and review | 21, 23, 24 |

## Grading

Graded with the [capstone rubric](../RUBRIC.md): seven dimensions, pass at 70/100 with at least 50 % in
both *Architecture and technical correctness* and *Measurement and analysis*, distinction at 90/100
with reproducible evidence. For Capstone A, excellent work looks like this:

| Dimension | What excellent looks like in Capstone A |
|---|---|
| Problem framing and assumptions (10) | The assumptions register ranks assumptions by sensitivity, and the top three (MFU, the DP overlap window, ECMP efficiency) each have a validation plan |
| Architecture and technical correctness (20) | Counts, cable media, power and cooling are correct. Option C is rejected on design rules, not only on price. Data paths are drawn from GPU to spine |
| Implementation / reproducibility (15) | All checks pass. One command regenerates every modeled number in the pack. Inputs are version-controlled |
| Measurement and analysis (20) | The layout × option × scenario table includes the launcher's real order, the sensitivity reaches a stated break-even, and modeled and measured values are never mixed |
| Reliability, security and operations (15) | Leaf blast radius is compared across options, the rack-05 and rack-08 constraints get owned mitigations, and the acceptance plan has entry and exit criteria |
| Troubleshooting and engineering judgment (10) | The pack recognizes that option B's penalty depends on the scheduler, says what would change the recommendation, and does not over-claim |
| Communication and portfolio quality (10) | A reviewer can follow the memo in five minutes and reproduce any number in thirty |

## File map

```text
capstone-a-256-gpu-training-cluster/
├── README.md            this brief
├── templates/           design pack, BOM, topology, workload model, power/cooling, acceptance, failure
│                        analysis, memo, ADR, facility checklist, results table, final review
├── starter-kit/         L1 design model: data/, tools/ (instructor edition only), starter/cluster_model.py, check.py, README.md
├── instructor/          grading guide, exemplar summary, reference implementation (removed in student edition)
└── review/REVIEW.md     editorial review log
```
