# Chapter 9 — Congestion Control and Lossless-Fabric Engineering

**Part III — Networking for AI Clusters · Course week 6 · Progressive Lab 3 (network telemetry)**

RoCEv2 AI fabrics depend on two cooperating mechanisms: Priority-based Flow Control (PFC), which
prevents loss by pausing senders, and ECN with DCQCN, which slows senders before PFC has to act. This
chapter teaches how both work at the level of queues, thresholds, and bytes; the arithmetic of
headroom, incast, and bandwidth-delay product on the ORION reference cluster; the failure modes PFC
introduces (head-of-line blocking, pause propagation, PFC storms, deadlock) and the watchdogs that
contain them; how to read congestion telemetry from switches and NICs; and where lossy RoCE and newer
transports such as Ultra Ethernet's change the picture. The lab turns a ten-minute synthetic telemetry
bundle into a congestion diagnosis, an experiment plan, and a mitigation proposal.

## Learning objectives

1. **Explain** how ECN marking, PFC pause, and DCQCN rate control interact on a RoCEv2 fabric, and which
   device plays each role.
2. **Calculate** the PFC headroom a port needs from link speed, cable length, MTU, and response time,
   and the incast fill time of a switch buffer.
3. **Choose and justify** ECN thresholds (Kmin, Kmax, Pmax) relative to the bandwidth-delay product.
4. **Diagnose** incast, pause propagation, PFC storms, and head-of-line (HOL) blocking from queue, ECN,
   CNP, pause, throughput, and latency telemetry.
5. **Explain** why enabling PFC indiscriminately creates operational risk, and describe how to
   investigate pause propagation and HOL blocking.
6. **Design** a controlled experiment that compares two documented congestion configurations, and
   **state** what a simulation cannot conclude.
7. **Write** a runbook excerpt with signals, thresholds, and safe actions for lossless-fabric incidents.

## Prerequisites

- Chapter 7 — ORION's rail-optimized leaf-spine, ECMP, DSCP.
- Chapter 8 — RDMA verbs and queue pairs, RoCEv2 encapsulation, go-back-N transport behaviour, DCQCN
  roles (introduced).
- Chapter 3 — host diagnostics (`lspci`, `ethtool`) used in the troubleshooting scenario.
- Python 3.10+ with `numpy`, `pandas`, `pyyaml` for the lab.

## Time budget

| Activity | Estimate |
|---|---|
| Reading the manuscript | 3.5–4 h |
| Exercises (knowledge, worked, outline, troubleshooting, design, reflection) | 4–5 h |
| Lab (L1) including the deliverable report | 4–6 h |
| Optional L3 extension (lab fabric) | 1 day |

## Lab tiers

- **L1 (required):** synthetic telemetry analysis and a SIMULATED fluid incast model — laptop, < 5 s.
- **L2 (optional):** map lab columns to real NIC counters on one RDMA host (read-only).
- **L3 (optional):** controlled incast A/B on a dedicated lab fabric with perftest and switch counters.

## Deliverable (course outline, week 6)

**Congestion diagnosis, experiment plan, and mitigation proposal** (Exercise H1, with O1–O3). The
congestion troubleshooting tree (Figure 9.10) is this chapter's half of the week-6 deliverable; the
physical-layer checklist comes from Chapter 10.

## File map

```text
ch09-congestion-control-lossless-fabrics/
├── README.md                    this chapter card
├── manuscript.md                chapter text (Sections 9.1–9.12 + operations, summary, reading)
├── exercises.md                 K1–K8, W1–W2, H1, O1–O3 (outline), T1, D1, R1–R4
├── lab/
│   ├── README.md                lab guide (Progressive Lab 3)
│   ├── manifest.yaml            environment manifest (L1; L3 fields to record)
│   ├── check.py                 python check.py [--impl starter|solution]
│   ├── data/                    synthetic telemetry, topology + QoS snapshot, sim configs
│   ├── tools/generate_telemetry.py   INSTRUCTOR ONLY: seeded generator (stripped from student release)
│   └── starter/congestion_lab.py     learner module with TODOs
├── solutions/                   INSTRUCTOR ONLY
│   ├── exercises-key.md         answers, marking guidance, planted anomalies
│   └── lab/                     congestion_lab.py (reference) + planted_faults.yaml (generator spec)
└── review/REVIEW.md             editorial review log
```

## Connections

Builds on Chapters 3, 7, 8. Applied in Chapter 10 (separating physical-layer faults from congestion),
Chapter 12 (collective slowdowns), Chapter 13 (rank-to-rail mapping), Chapter 15 (KV-cache transfer
incast), Chapter 18 (dashboards and alerts), and **Capstone B** (AI network troubleshooting and
telemetry system).
