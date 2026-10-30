# Chapter 19 — Reliability, Security, and Multi-Tenancy

**Part V — Operating Production AI Infrastructure · Course week 12**

At ORION-XL scale a 4,096-GPU job is interrupted about every three hours. This chapter treats failure
as the operating environment: fault domains and FMEA; the GPU/host error taxonomy (ECC, row remapping,
Xid, thermal/power, PCIe AER, link retraining, NIC/HCA health, firmware mismatch); distributed failure
signatures (NCCL hangs, rank loss, collective mismatch, stragglers, partitions); the fast isolation
workflow from rank to switch port; containment of the smallest defensible failure domain; and recovery
with validated checkpoints, rank remapping, spares, retry-loop policy, RTO/RPO, and lost
accelerator-hours. The second half covers identity, RBAC, secrets, network/storage/GPU isolation, and
audit for multi-tenant platforms.

## Learning objectives

1. **Calculate** job MTBF, checkpoint-interval trade-offs, and goodput from node failure rates.
2. **Perform** and **critique** an FMEA across GPU, node, rack, leaf, PDU, CDU, storage, scheduler, and
   control-plane domains.
3. **Classify** GPU and host errors and **choose** the correct action.
4. **Diagnose** distributed failure signatures from flight-recorder, log, and counter evidence.
5. **Correlate** rank → GPU UUID → BDF → NUMA → HCA → switch port → counters → logs → scheduler, and
   **distinguish** proven cause from correlation.
6. **Design** containment and recovery with RTO/RPO and lost accelerator-hours.
7. **Define** and **audit** tenant isolation boundaries.

## Prerequisites

Chapters 5, 8–10, 12, 14, 16, 17, and 18.

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3.5 h |
| Exercises | 3.5 h |
| Lab (L1) | 4 h |
| L2/L3 extension (optional) | 3–6 h |

## Lab tier

**L1** (synthetic ORION-XL incident, `[SIMULATED]`); optional **L2** (read-only GPU health on one host)
and **L3** (link-flap survival trials on a dedicated RDMA partition).

## Deliverable (course outline)

Risk register, isolation model, and recovery test plan (M1–M3), plus the Section 20.1 evidence pack
from the 512-node incident (M4 / Lab 19).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Exercises including outline-mandated M1–M4 |
| [lab/README.md](lab/README.md) | Lab guide |
| `lab/data/` | Incident dataset (`lab/tools/` generator: instructor copy only) |
| `lab/starter/incident_toolkit.py` | Learner module |
| `lab/check.py`, `lab/manifest.yaml` | Checker and environment manifest |
| `solutions/` | Answer key and reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Uses Chapter 18's correlation keys and incident practice; feeds Chapter 20 (automated remediation,
rate-limited quarantine), Chapter 21 (spare reserve), Chapter 23, and Capstones F and G.
