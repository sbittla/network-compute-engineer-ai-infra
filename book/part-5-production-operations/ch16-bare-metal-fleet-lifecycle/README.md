# Chapter 16 — Bare-Metal GPU Fleet Lifecycle

**Part V — Operating Production AI Infrastructure · Course week 7 · Progressive Lab 7 (part 1)**

A GPU cluster is rebuilt every day: nodes are discovered, imaged, accepted, scheduled, drained,
repaired, upgraded, and retired. In a synchronous training job one subtly broken node taxes every
other GPU, so each lifecycle transition must be guarded and audited. This chapter covers the
inventory/CMDB, out-of-band control through the BMC (IPMI and Redfish), PXE/iPXE imaging and
provisioning systems, node acceptance (GPU discovery, DCGM diagnostics, HBM ECC and row remapping,
NVLink/NVSwitch, PCIe width, NIC speed and RDMA pair tests, storage, thermals, burn-in, single-node
NCCL), firmware/driver compatibility bundles, staged upgrades with canaries and waves, drain/repair/
RMA, and decommissioning with media sanitization — all on the ORION reference cluster.

## Learning objectives

1. Explain the node lifecycle and design guarded transitions with an append-only audit trail.
2. Operate a node out-of-band through IPMI and Redfish, and explain PXE → iPXE → HTTP provisioning.
3. Design a fail-fast node acceptance test covering GPU, HBM, NVLink, PCIe, NIC/RDMA, storage,
   thermals, burn-in, and single-node NCCL.
4. Diagnose acceptance failures from raw evidence and separate real defects from normal behaviour.
5. Build a bundle-style compatibility matrix and calculate a staged upgrade plan with explicit blast
   radius and capacity loss.
6. Plan drain, repair, RMA, and decommissioning with re-acceptance and sanitization evidence.
7. Quantify the cost of a single degraded node in a synchronous training job on ORION.

## Prerequisites

Chapter 3 (host diagnostics), Chapter 5 (host topology, GPU↔NIC locality), Chapter 8 (RDMA and
perftest), Chapter 10 (optics and link commissioning), Chapter 12 (`all_reduce_perf`, bus bandwidth).

## Time budget

| Activity | Estimate |
|---|---|
| Reading | 2.5–3 h |
| Exercises (excluding deliverable) | 4–5 h |
| Lab (L1) | 3–4 h |
| Deliverable D1 | 3–4 h |

## Lab tier

L1 required (laptop; synthetic ORION data). L2 (single GPU host) and L3 (multi-node RDMA) extensions
in [lab/README.md](lab/README.md).

## Deliverable (from the course outline)

**Node acceptance automation specification and lifecycle runbook** — exercise D1 in
[exercises.md](exercises.md).

## File map

| Path | Content |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Knowledge checks, worked problems, lab, troubleshooting, design, outline-mandated exercises M1–M3, deliverable D1 |
| [lab/README.md](lab/README.md) | Lab guide (tasks, rubric, L2/L3 extension) |
| `lab/manifest.yaml` | Environment manifest |
| `lab/data/` | Acceptance policy, compatibility matrix, acceptance results, inventory, lifecycle events |
| `lab/tools/generate_data.py` | Deterministic generator (seed 16) — instructor copy only; stripped from the student release |
| `lab/starter/fleet_lifecycle.py` | Learner module with TODOs |
| `lab/check.py` | Checker: `python check.py [--impl starter|solution]` |
| `lab/report.py` | Markdown report from your implementation (Task 5) |
| `solutions/` | Instructor-only answer key, reference implementation, planted-fault list |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Feeds Chapter 17 (scheduler eligibility), Chapter 18 (health signals), Chapter 19 (fault isolation
and quarantine), Chapter 20 (safe change and rollout), and Capstones E and G.
