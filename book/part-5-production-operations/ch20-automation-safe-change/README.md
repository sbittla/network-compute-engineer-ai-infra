# Chapter 20 — Infrastructure Automation and Safe Change

**Part V — Operating Production AI Infrastructure · Course week 13**

Automation is how a small team changes a 256-GPU cluster, and the fastest way to break all of it.
This chapter covers the engineering that makes fleet change safe. It starts with the languages and
APIs automation drives (Redfish, gNMI/OpenConfig, NETCONF/YANG, the Kubernetes API), then covers
idempotent desired-state reconciliation, infrastructure as code (plan, apply, state, drift), and
layered validation with policy-as-code. From there it moves to CI/CD and GitOps, staged rollout
with canaries, waves, bake time, and pre-declared abort conditions, then rollback and
roll-forward, fleet-safety controls (dry run, blast-radius caps, rate limits, kill switches,
circuit breakers), and audit evidence. The running example is raising the RDMA MTU on ORION from
1,024 to 4,096 and rolling out a NIC firmware bundle in waves.

## Learning objectives

1. **Explain** idempotency, desired-state reconciliation, and drift, and **write** a reconciler
   whose second run is provably a no-op.
2. **Design** a validation pipeline (syntax → schema → cross-object policy → pre-deployment
   analysis → post-deployment verification), and **calculate** the MTU budget a RoCEv2 fabric
   requires.
3. **Compare** imperative scripts, IaC, configuration management, and GitOps controllers, and
   **choose** among them.
4. **Design** a canary rollout with prechecks, wave sizes, bake time, success criteria, abort
   conditions, rollback scope, and audit evidence.
5. **Calculate** detection probability, capacity impact, and duration for a wave plan on ORION.
6. **Apply** fleet-safety controls and **justify** their thresholds.
7. **Diagnose** an automation-caused incident from audit logs, controller logs, and counters.
8. **Review** a change plan and **identify** missing validation, blast-radius controls, and rollback.

## Prerequisites

Chapters 7–9 (ORION fabric, RDMA MTU, RoCE QoS: DSCP 26 → TC 3 with PFC, CNP DSCP 48 → TC 6),
Chapter 16 (lifecycle states, compatibility matrices, firmware waves), and Chapter 17 (drain and
reservations). You also need Python 3.10+ and basic git.

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3.5 h |
| Exercises | 5 h |
| Lab (L1) | 3 h (+2–4 h for L2/L3 extensions) |

## Lab tier

**L1** (laptop, simulated fleet and telemetry). Optional **L2** (real host MTU/RDMA reconciler on a
lab VM) and **L3** (canary evidence from `all_reduce_perf` pair tests and NIC/switch counters on a
lab fabric).

## Deliverable

**Automation sample and safe-change runbook** (Exercise 20.10), built from Lab 20 Parts 1–2 and
the runbook excerpt in the manuscript.

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Standard exercise set + outline-mandated exercises + deliverable |
| [lab/README.md](lab/README.md) | Lab guide (Parts 1–3, rubric, L2/L3 extensions) |
| `lab/manifest.yaml` | Environment manifest |
| `lab/data/` | Desired/actual state, rollout evidence, abort conditions, unsafe plan, gap catalogue |
| `lab/tools/generate_data.py` | Instructor copy only (stripped from the learner release); seeded (20) generator |
| `lab/starter/` | `safe_change.py` (TODOs) and `findings.yaml` template |
| `lab/check.py` | Checker: `python check.py [--impl starter\|solution]` |
| `solutions/` | Instructor-only answer key and reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds on [Chapter 16](../ch16-bare-metal-fleet-lifecycle/) and
[Chapter 17](../ch17-kubernetes-slurm-scheduling/). It feeds
[Chapter 18](../ch18-observability-slos-incident-response/) (rollout signals, "what changed?"),
[Chapter 19](../ch19-reliability-security-multitenancy/) (blast radius, remediation budgets), and
Capstones E and F in [capstones/](../../../capstones/).
