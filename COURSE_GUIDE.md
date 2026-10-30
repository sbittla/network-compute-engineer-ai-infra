# Course Guide — 14-Week Program

This guide turns the 24-chapter book into a 14-week course. Each week lists the chapters to read, the
lab to complete, and the deliverable to submit. Lab tiers: **L1** laptop/simulation (required),
**L2** single GPU host (optional), **L3** multi-node GPU + RDMA/InfiniBand (optional).

## Weekly plan

| Wk | Module | Read | Lab(s) | Deliverable |
|---|---|---|---|---|
| 1 | AI data-center architecture and economics | Ch 1, Ch 2 | [ch01 lab](book/part-1-foundations/ch01-ai-infrastructure-landscape/lab/), [ch02 lab](book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/lab/) | Architecture diagram, workload assumptions, rack power/thermal budget |
| 2 | Linux, host systems and diagnostics | Ch 3 | [ch03 lab](book/part-1-foundations/ch03-linux-host-systems-diagnostics/lab/) — **Progressive Lab 1** | Host diagnostic runbook and baseline |
| 3 | GPU compute and interconnects | Ch 4, Ch 5, Ch 6 | ch04–ch06 labs — **Progressive Lab 4** | GPU profiling exercise, topology map, GPU-to-NIC mapping CSV |
| 4 | Ethernet, L2/L3 and BGP fabrics | Ch 7 | ch07 lab — **Progressive Lab 2** | Fabric design and failure-convergence analysis |
| 5 | RDMA, RoCEv2 and InfiniBand | Ch 8 | ch08 lab | RDMA design note and readiness checklist |
| 6 | Congestion, switching and physical layer | Ch 9, Ch 10 | ch09, ch10 labs — **Progressive Lab 3** | Congestion troubleshooting tree and physical-layer checklist |
| 7 | Bare-metal provisioning and fleet lifecycle | Ch 16 | ch16 lab — **Progressive Lab 7 (part 1)** | Node acceptance checklist and lifecycle workflow |
| 8 | Kubernetes, Slurm and workload placement | Ch 17 | ch17 lab — **Progressive Lab 7 (part 2)** | Scheduling policy and pending-job troubleshooting guide |
| 9 | Distributed training and NCCL | Ch 11, Ch 12, Ch 13 | ch11–ch13 labs — **Progressive Lab 5** | Collective benchmark and scaling analysis |
| 10 | LLM inference and serving | Ch 15 | ch15 lab | Inference capacity model, KV-transfer model, tuning recommendation |
| 11 | Storage, data movement and checkpointing | Ch 14 | ch14 lab — **Progressive Lab 6** | Checkpoint/data-pipeline design with RPO/RTO analysis |
| 12 | Observability, SLOs and reliability | Ch 18, Ch 19 | ch18, ch19 labs — **Progressive Lab 8** | Dashboard spec, incident report, fault-isolation runbook |
| 13 | Automation, security and capacity | Ch 20, Ch 21 | ch20, ch21 labs | Automated change plan, capacity/power/cooling model |
| 14 | Integrated capstone and technical review | Ch 22, Ch 23, Ch 24 | Capstone (A–H) | Portfolio-ready architecture, runbook, benchmark report |

## Progressive lab sequence

The eight progressive labs from the course outline are delivered by chapter labs:

| Progressive lab | Delivered by |
|---|---|
| Lab 1 — Host discovery | Chapter 3 lab (plus Chapter 5 topology mapping) |
| Lab 2 — Fabric design | Chapter 7 lab |
| Lab 3 — Network telemetry | Chapter 9 lab (plus Chapter 10 physical-layer counters) |
| Lab 4 — GPU baseline | Chapter 4 and Chapter 6 labs |
| Lab 5 — Distributed communication | Chapter 12 lab (plus Chapters 11 and 13) |
| Lab 6 — Storage and checkpoint | Chapter 14 lab |
| Lab 7 — Scheduler and fleet lifecycle | Chapter 16 and Chapter 17 labs |
| Lab 8 — Observability and incident | Chapter 18 lab |

## Assessment

| Assessment | Weight | Evidence |
|---|---|---|
| Knowledge checks and design reviews | 15% | Accurate concepts, architecture and trade-off explanations |
| Hands-on labs and troubleshooting | 30% | Reproducible diagnostics, configurations/simulations, root-cause reasoning |
| Performance and benchmark assignments | 20% | Valid methodology, baselines, repeatability, percentile analysis, conclusions |
| Capstone project | 35% | Integrated architecture, operational plan, failure exercise, measured results, communication |

Completion requires demonstrated competence: learners must explain design trade-offs, troubleshoot
at least one cross-layer failure, and support every performance claim with reproducible evidence.
Capstone scoring: see [capstones/RUBRIC.md](capstones/RUBRIC.md) (pass ≥ 70/100 with no score below
50 % in technical correctness or measurement; distinction ≥ 90/100 with reproducible evidence).

## Role-specific pathways

| Role | Core chapters (go deep) | Recommended capstone | Electives |
|---|---|---|---|
| AI Network Engineer | 7, 8, 9, 10, 13 | B (telemetry) or A (fabric option) | Advanced fabric design; RDMA tuning; network operations |
| GPU Compute / HPC Engineer | 4, 5, 6, 12, 13 | C (training performance) | GPU profiling; collectives; accelerator topology |
| AI Cluster / Platform Engineer | 16, 17, 19, 20 | E (fleet lifecycle) or G | Fleet automation; scheduler internals; capacity |
| AI Performance Engineer | 6, 12, 15, 22 | C or H | Roofline; distributed scaling; inference performance |
| AI Infrastructure SRE / Operations | 18, 19, 20, 22 | F (game day) or G | Incident simulation; fault injection; automated recovery |
| Network Hardware / Vendor Engineer | 9, 10, 8 | B with L3 extension | Hardware validation; congestion characterisation; interoperability |

## Instructor notes

- Starter files, sample telemetry, expected outputs, and grading rubrics are in every `lab/` folder.
- Answer keys live in each chapter's `solutions/` folder and in `capstones/*/instructor/`. Remove these
  folders before distributing to learners (`scripts/make_student_release.py`).
- Many datasets contain intentionally planted faults; the planted-fault list is in `solutions/`.
- Safety: no production changes, disruptive fault injection, or changes to shared fabrics without
  authorisation and an isolated test environment.
