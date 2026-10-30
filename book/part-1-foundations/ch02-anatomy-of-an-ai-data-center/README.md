# Chapter 2 — Anatomy of an AI Data Center

**Part I — Foundations · Course week 1 (with Chapter 1)**

A GPU cluster is a building-scale machine. This chapter takes the ORION reference cluster apart from
the GPU to the utility feed: the HX8 server and where its 10.2 kW goes; racks, rows, and floor layout;
the backend, frontend, and out-of-band networks and their bill of materials; the power chain (UPS,
busway, PDUs, power shelves, PSUs) and redundancy modes; TDP, synchronised transients, and power
capping; air versus direct-to-chip liquid cooling with CDUs and `Q = ṁ · cp · ΔT` arithmetic; MEP
interfaces, floor loading, commissioning, and ownership; and capacity, utilization, failure domains,
and a first look at cost. Every figure is tied to stated assumptions, and the lab turns the chapter
into a reusable capacity/BOM/power/SPOF model that catches flawed planning sheets.

## Learning objectives

1. **Explain** the physical hierarchy of an AI data center and its three networks (backend,
   frontend, out-of-band).
2. **Calculate** a cluster bill of materials: servers, rack units, switches, ports, links,
   transceivers, and bisection bandwidth.
3. **Calculate** a rack power budget: three-phase circuit capacity, derating, power factor, transient
   margin, redundancy mode, and power-supply feed loss.
4. **Calculate** a heat-removal budget using `Q = ṁ · cp · ΔT` for both liquid and air, and convert
   it into coolant flow (L/min), airflow (CFM), and CDU loading.
5. **Diagnose** a facility-coupled performance problem (thermal or power throttling) using GPU,
   scheduler, and facility telemetry together.
6. **Design** an assumptions register and a facility/MEP handoff checklist for a high-density rack.
7. **Identify** single points of failure in a cluster design, including ones hidden in power paths,
   and propose mitigations with an explicit accept/fix decision.

## Prerequisites

[Chapter 1](../ch01-ai-infrastructure-landscape/README.md); basic electrical literacy (watts, volts,
amps); Python 3.10+ for the lab. No GPU, facility access, or root needed for the core material.

## Time budget

| Activity | Time |
|---|---|
| Reading `manuscript.md` (≈ 10,000 words incl. tables, code, and diagrams) | 2.5–3 h |
| Exercises 2.1–2.3, 2.5–2.7, 2.11 | 3–4 h |
| Exercises 2.9–2.10 (design challenges) | 3 h |
| Lab (L1) | 2–3 h |
| Optional L2/L3 extensions (Exercise 2.8, lab Section 8) | 2–4 h |

## Lab tier

**L1** (laptop, < 5 s runtime, deterministic synthetic data). Optional **L2** (one GPU server with BMC
access: measured power profile, power-cap sweep) and **L3** (rack PDU and CDU telemetry with
facilities sign-off).

## Deliverable (course outline)

Cluster bill of materials, capacity spreadsheet, and failure-domain diagram — plus (definitive-edition
enhancement, outline §20.3/§21) a rack power/thermal budget with assumptions register and a facility
interface diagram / MEP handoff checklist. See [exercises.md](exercises.md#chapter-deliverable).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Exercises 2.1–2.11 with difficulty, tier, and evidence required |
| [lab/README.md](lab/README.md) | Lab guide: ORION capacity, BOM, power/cooling, and SPOF model |
| `lab/manifest.yaml` | Environment manifest (tier, deps, seed, L2/L3 record fields) |
| `lab/data/` | Six input sheets (generated, committed) |
| `lab/tools/` | Instructor-only seeded generator (stripped from the student release) |
| `lab/starter/capacity_model.py` | Learner module (functions raise `NotImplementedError`) |
| `lab/check.py` | Checker: `python check.py [--impl starter\|solution]` |
| `solutions/exercises-key.md` | Instructor answer key, planted-flaw list, marking guidance |
| `solutions/lab/capacity_model.py` | Reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Course week

Week 1 — *AI data-center architecture and economics* (Chapters 1 and 2). Week deliverable:
architecture diagram, workload assumptions, rack power/thermal budget.
