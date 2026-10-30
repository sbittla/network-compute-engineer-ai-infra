# Chapter 18 — Observability, SLOs, and Incident Response

**Part V — Operating Production AI Infrastructure · Course week 12 · Progressive Lab 8**

AI clusters fail quietly: one throttled GPU, one flapping link, or one bad switch profile stretches
every synchronous training step without a single error message. This chapter builds the
observability system that catches those failures — GPU (DCGM), host, NIC/RDMA, switch (gNMI
streaming), scheduler, workload, logs, and traces — and turns it into SLIs, SLOs, and multiwindow
burn-rate alerts, a fleet → node → device → workload dashboard hierarchy, and an incident-command and
blameless-postmortem practice. The running case is INC-2291, a cluster-wide training-throughput
regression on ORION that no alert caught.

## Learning objectives

1. **Explain** what each telemetry layer can and cannot reveal, and why `GPU utilization` misleads for
   synchronous training.
2. **Write** PromQL queries, recording rules, and alert rules for GPU fleets, and **estimate**
   cardinality and resolution needs.
3. **Define** SLIs and SLOs for training goodput and completion, inference latency, cluster
   availability, and fabric health, and **calculate** error budgets and burn rates.
4. **Design** symptom-based multiwindow burn-rate alerts and **evaluate** a rule set for noisy and
   missing alerts.
5. **Design** a dashboard hierarchy with explicit drill-down keys.
6. **Run** an incident with defined roles, severities, and comms cadence; **construct** a timeline
   with TTD, TTM, and TTR.
7. **Write** an evidence-based blameless postmortem with typed, owned action items.

## Prerequisites

Chapters 4, 5, 9, 10, 12, 14, 15, and 17 (GPU execution, host topology, congestion control, physical
layer, collectives, checkpointing, serving metrics, scheduling). Comfortable with Python and pandas.

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3.5 h |
| Exercises | 3 h |
| Lab (L1) | 4 h |
| L2/L3 extension (optional) | 4–8 h |

## Lab tier

**L1** (laptop, synthetic telemetry bundle, `[SIMULATED]`). Optional **L2** (one GPU host with DCGM,
dcgm-exporter, Prometheus) and **L3** (multi-node RDMA with read-only switch gNMI access).

## Deliverable (course outline)

SLO specification, dashboard mock-up, and blameless postmortem (Exercises M1–M3; Lab 18).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Knowledge checks, worked problems, lab, troubleshooting, design, reflection, outline-mandated M1–M3 |
| [lab/README.md](lab/README.md) | Lab guide: telemetry-bundle forensics |
| `lab/data/` | Synthetic bundle: step records, node/switch metrics, inference SLO counts, events, alert rules, postmortem template |
| `lab/tools/` | Data generator — instructor copy only (not in the student release) |
| `lab/starter/telemetry_analysis.py` | Learner module (TODOs) |
| `lab/check.py` | Checker: `python check.py [--impl starter\|solution]` |
| `lab/manifest.yaml` | Environment manifest |
| `solutions/` | Instructor answer key and reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Builds on Chapters 9 (ECN/PFC/DCQCN), 12 (collectives), and 17 (schedulers). Feeds Chapter 19 (fault
isolation uses these correlation keys), Chapter 20 (SLOs as change-abort criteria), Chapter 21
(utilization and goodput), Chapter 22 (cross-layer diagnosis), and Capstones B, F, and G.
