# Capstone Program

The capstone is where the book's method becomes your own evidence: observe a symptom, collect
evidence, trace the bottleneck across compute, network, storage and orchestration, find the root
cause, make a safe change, and validate it with repeatable measurements. Each project is set on
**ORION** ([docs/REFERENCE_CLUSTER.md](../docs/REFERENCE_CLUSTER.md)), the 256-GPU cluster run by
Halcyon AI (or its 4,096-GPU scale-out variant, ORION-XL), so your numbers can be checked against the
rest of the book. Every capstone ships a runnable Level-1 starter kit, so a laptop is enough to earn a
distinction. Hardware-backed (L2/L3) extensions turn modeled or simulated claims into measured ones.

The capstone is worth **35 %** of the course assessment ([COURSE_GUIDE.md](../COURSE_GUIDE.md)) and is
the deliverable for [Chapter 23](../book/part-6-applied-engineering/ch23-capstone-production-ai-cluster/).

## 1. How to choose

Complete **one primary capstone**. Optionally, add **one specialization mini-capstone**: a second
capstone done at reduced scope (its starter kit plus three of its artifacts of your choice, graded on
R3, R4 and R6 only, as a subtotal out of 45 with a pass at ≥ 32/45 and R4 ≥ 10). The mini-capstone is
recorded separately as a specialization credit and does not change the 35 % capstone weight
([RUBRIC.md §4](RUBRIC.md#4-specialization-mini-capstone)). Use it to show breadth for a target role.

| If you are aiming at… | Primary | Good mini-capstone |
|---|---|---|
| AI infrastructure architect / cluster engineer | A | D or F |
| AI network engineer / network operations | B | A (fabric options) |
| GPU/HPC or AI performance engineer | C | D or H |
| AI platform / inference infrastructure engineer | D | H |
| Cluster platform engineer / infrastructure SRE | E | G |
| AI infrastructure SRE / production engineer | F | G or B |
| Large-scale training operations | G | C |
| Advanced inference / serving architecture | H | D |

Choose by Week 8. Changing after Milestone M1 (Week 10) needs instructor approval.

## 2. The eight capstones

| ID | Capstone | Audience (course outline Section 16; G and H suggested, as Section 22 names none) | Starter kit centrepiece |
|---|---|---|---|
| A | [Design a 256-GPU AI training cluster](capstone-a-256-gpu-training-cluster/) | AI infrastructure architect, cluster engineer, network engineer | Design model: BOM, cable plan, power/cooling, rank-layout oversubscription, cost per token |
| B | [Build an AI network troubleshooting and telemetry system](capstone-b-network-telemetry-troubleshooting/) | AI Network Engineer, Network Operations Engineer | Multi-format counter parser, wrap/reset-aware rates, root-cause alert rules scored for precision/recall |
| C | [Distributed training performance optimization](capstone-c-distributed-training-performance/) | GPU/HPC engineer, AI Performance Engineer | CPU-proxy benchmark harness; admissibility, weak scaling and significance on supplied runs |
| D | [Production LLM inference platform](capstone-d-llm-inference-platform/) | AI Platform Engineer, Inference Infrastructure Engineer | Capacity model + discrete-event continuous-batching simulator, SLO gates, cost |
| E | [Bare-metal GPU fleet lifecycle automation](capstone-e-fleet-lifecycle-automation/) | Cluster Platform Engineer, Infrastructure SRE | Lifecycle state machine and automation prototype |
| F | [AI infrastructure reliability game day](capstone-f-reliability-game-day/) | AI Infrastructure SRE, Production Engineer | Fault-injection plan, telemetry, incident timeline, postmortem |
| G | [Fault-tolerant 512-node distributed training operations](capstone-g-fault-tolerant-512-node-training/) | Training operations, SRE, platform engineers | Telemetry correlation, quarantine, checkpoint/restore on ORION-XL |
| H | [Disaggregated LLM serving across prefill and decode pools](capstone-h-disaggregated-llm-serving/) | Inference and performance engineers | KV-transfer model, RDMA/TCP comparison, phase SLOs |

## 3. Required sections in every project

Course outline, Section 16: every capstone submission contains these nine sections, plus the
capstone-specific artifacts listed in its README.

| Section | What it must contain |
|---|---|
| Problem statement | The decision or system to deliver, constraints, testable success criteria, scope |
| Architecture | Diagram(s) with captions; components, data paths, failure domains, trust boundaries |
| Assumptions | An assumptions register with values, evidence labels, sensitivity and how each would be validated |
| Implementation or simulation boundary | What was built or simulated, at which tier, and what it cannot show |
| Test plan | What is tested, how, with which pass criteria and evidence |
| Results | Tables and charts with `[MEASURED]` / `[MODELED]` / `[SIMULATED]` / `[ILLUSTRATIVE]` labels, kept apart |
| Failure analysis | Failure modes, detection, blast radius, mitigation and recovery |
| Security considerations | Concrete controls for the system you designed |
| Final engineering review | Self-score against the rubric, peer-review findings, prioritized backlog, reproducibility statement |

Templates for all of them are in each capstone's `templates/` folder.

## 4. Tiers

| Tier | Environment | Role in the capstone |
|---|---|---|
| **L1** | Laptop; Python 3.10+ with `requirements.txt` | Required. Starter kit, models, simulations, analysis of supplied data. Distinction is achievable |
| **L2** | One GPU host or one 8-GPU node | Optional. Converts host-level assumptions into `[MEASURED]` evidence |
| **L3** | ≥ 2 GPU nodes with RDMA (RoCEv2 or InfiniBand) and switch access | Optional. Converts fabric and multi-node claims into `[MEASURED]` evidence |

> **Safety:** All fault injection, load tests and configuration experiments run in a simulator or on
> dedicated lab hardware you are authorized to use, never on shared or production systems.

## 5. Timeline

The capstone is presented in **Week 14**, but the work starts earlier.

| Milestone | Week | Deliverable | Feedback |
|---|---|---|---|
| M0: choose | 8 | Capstone choice; read the brief and the starter-kit data | Instructor confirms fit with role goal |
| M1: proposal | 10 | Problem statement, assumptions register v1, architecture sketch, first starter-kit checks passing | 15-minute design review |
| M2: core build | 12 | Starter kit (most or all checks) and core analysis | Written feedback on method |
| M3: draft | 13 | All artifacts in draft; peer review scheduled | Peer review (use `templates/final-engineering-review.md`) |
| M4: final | 14 | Complete submission + 15-minute presentation + 10-minute questions | Graded with the [rubric](RUBRIC.md) |

Week 14 itself: day 1–2 final edits and reproducibility check; day 3–4 presentations; day 5 viva
follow-ups and grading.

## 6. Grading

[RUBRIC.md](RUBRIC.md): seven weighted dimensions. Pass ≥ 70/100 with at least 50 % in *Architecture
and technical correctness* and in *Measurement and analysis*. Distinction ≥ 90/100 with reproducible
evidence. Each capstone README describes what excellent looks like for that project.

## 7. Submission checklist

- [ ] All nine required sections present (Section 3)
- [ ] Every capstone-specific artifact in the brief's "Required artifacts" table
- [ ] `python check.py` in your starter kit: output pasted into the submission, with all checks passing
      (or each failure explained)
- [ ] One command (or a short script) regenerates every `[MODELED]`/`[SIMULATED]` number in the report
- [ ] Every number labelled; no `[SIMULATED]` or `[MODELED]` value presented as measured
- [ ] Every `[MEASURED]` value has an environment manifest, warm-up policy and ≥ 5 repetitions with spread
- [ ] Diagrams captioned; units consistent (Gb/s for links, GB/s or GiB for memory, stated directionality)
- [ ] Canonical ORION names used (`orion-nNN`, `rack-NN`, `orion-be-leaf-rR`, `orion-be-spine-S`)
- [ ] Safety: no instruction that would change shared or production systems
- [ ] Final engineering review with self-score, peer findings and prioritized backlog
- [ ] Slides (≤ 12) for the 15-minute presentation

## 8. Instructor material

Each capstone has an `instructor/` folder (grading guide with planted issues and reference numbers,
exemplar summary of a distinction-level submission, and a reference implementation that passes
`check.py --impl solution`). `scripts/make_student_release.py` removes these folders. Validate all
starter kits with:

```bash
python scripts/validate_labs.py capstone
```
