# AI Infrastructure Engineering

**From GPU Compute and High-Speed Networking to Distributed Training, LLM Inference, and
Production-Scale AI Systems**

A practical, systems-oriented book and 14-week course for engineers who design, build, operate, and
optimize AI infrastructure. It treats AI infrastructure as one connected discipline: workloads are
followed across accelerators and host topology, high-speed fabrics, collective communication, storage,
orchestration, observability, reliability, facilities, and cost.

> **The diagnostic loop:** observe a workload symptom → collect evidence → trace the bottleneck across
> compute, network, storage, and orchestration → identify root cause → make a safe change → validate
> the result with repeatable measurements.

## Who it is for

Network engineers moving into AI fabrics (RoCEv2, InfiniBand); Linux/HPC/data-centre engineers
supporting GPU fleets; ML platform, MLOps, and SRE engineers operating training and inference;
performance engineers; and architects targeting hyperscalers, neoclouds, frontier AI labs, and
hardware vendors. Prerequisites: Linux CLI, Python, IP networking, general systems knowledge.

## Repository layout

```text
.
├── README.md                 ← you are here
├── COURSE_GUIDE.md           ← 14-week plan, progressive labs, assessment, role pathways
├── requirements.txt          ← Python deps for all Level-1 labs
├── docs/
│   ├── STYLE_GUIDE.md        ← editorial + technical standards (evidence labels, units, terminology)
│   ├── CHAPTER_TEMPLATE.md   ← required structure for every chapter package
│   ├── EDITORIAL_RUBRIC.md   ← 9-dimension review rubric and 9.5 release gate
│   ├── LAB_STANDARDS.md      ← lab tiers, manifests, check.py contract, benchmark discipline
│   ├── REFERENCE_CLUSTER.md  ← ORION: the running-example cluster used in every chapter
│   ├── RELEASE_GATES.md      ← external validation still required before publication
│   ├── REVIEW_STATUS.md      ← per-package review scores and open findings
│   ├── VERIFIED_FACTS.md     ← reviewer-verified facts and book-wide corrections
│   └── COURSE_OUTLINE_SOURCE.md
├── book/
│   ├── part-1-foundations/               Ch 1–3
│   ├── part-2-accelerated-compute/       Ch 4–6
│   ├── part-3-networking/                Ch 7–10
│   ├── part-4-distributed-ai/            Ch 11–15
│   ├── part-5-production-operations/     Ch 16–22
│   └── part-6-applied-engineering/       Ch 23–24
│       └── chNN-slug/
│           ├── README.md       chapter card
│           ├── manuscript.md   chapter text
│           ├── exercises.md    standard exercise set
│           ├── lab/            runnable lab (starter, data, generators, check.py)
│           ├── solutions/      instructor answer key + reference lab solution
│           └── review/         editorial review log
├── capstones/                Capstones A–H, rubric, starter kits, instructor guides
└── scripts/
    ├── validate_labs.py      ← verifies every lab (solution passes, starter fails gracefully)
    └── make_student_release.py
```

## Table of contents

| Part | Chapter |
|---|---|
| **I — Foundations** | [1. The AI Infrastructure Landscape](book/part-1-foundations/ch01-ai-infrastructure-landscape/) · [2. Anatomy of an AI Data Center](book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/) · [3. Linux, Host Systems, and Performance Diagnostics](book/part-1-foundations/ch03-linux-host-systems-diagnostics/) |
| **II — Accelerated Compute** | [4. GPU Architecture and CUDA Execution](book/part-2-accelerated-compute/ch04-gpu-architecture-cuda-execution/) · [5. GPU Interconnects and Host Topology](book/part-2-accelerated-compute/ch05-gpu-interconnects-host-topology/) · [6. GPU Performance Engineering](book/part-2-accelerated-compute/ch06-gpu-performance-engineering/) |
| **III — Networking for AI Clusters** | [7. Ethernet and Data-Center Network Foundations](book/part-3-networking/ch07-ethernet-datacenter-network-foundations/) · [8. RDMA, RoCEv2, and InfiniBand](book/part-3-networking/ch08-rdma-rocev2-infiniband/) · [9. Congestion Control and Lossless-Fabric Engineering](book/part-3-networking/ch09-congestion-control-lossless-fabrics/) · [10. Switches, Optics, Cabling, and Physical-Layer Operations](book/part-3-networking/ch10-switches-optics-physical-layer/) |
| **IV — Distributed AI Systems** | [11. Distributed Training Architecture](book/part-4-distributed-ai/ch11-distributed-training-architecture/) · [12. Collective Communication and NCCL](book/part-4-distributed-ai/ch12-collective-communication-nccl/) · [13. GPU-to-GPU and GPU-to-NIC Data Movement](book/part-4-distributed-ai/ch13-gpu-data-movement/) · [14. Storage, Data Pipelines, and Checkpointing](book/part-4-distributed-ai/ch14-storage-pipelines-checkpointing/) · [15. LLM Inference and Serving Infrastructure](book/part-4-distributed-ai/ch15-llm-inference-serving/) |
| **V — Operating Production AI Infrastructure** | [16. Bare-Metal GPU Fleet Lifecycle](book/part-5-production-operations/ch16-bare-metal-fleet-lifecycle/) · [17. Kubernetes, Slurm, and Workload Scheduling](book/part-5-production-operations/ch17-kubernetes-slurm-scheduling/) · [18. Observability, SLOs, and Incident Response](book/part-5-production-operations/ch18-observability-slos-incident-response/) · [19. Reliability, Security, and Multi-Tenancy](book/part-5-production-operations/ch19-reliability-security-multitenancy/) · [20. Infrastructure Automation and Safe Change](book/part-5-production-operations/ch20-automation-safe-change/) · [21. Capacity, Power, and Infrastructure Economics](book/part-5-production-operations/ch21-capacity-power-economics/) · [22. Cross-Layer Performance Engineering](book/part-5-production-operations/ch22-cross-layer-performance-engineering/) |
| **VI — Applied Engineering** | [23. Capstone: Design and Operate a Production-Scale AI Cluster](book/part-6-applied-engineering/ch23-capstone-production-ai-cluster/) · [24. Career Paths and Engineering Practice](book/part-6-applied-engineering/ch24-career-paths-engineering-practice/) |
| **Capstones** | [Overview](capstones/README.md) · [Rubric](capstones/RUBRIC.md) · [A. 256-GPU training cluster](capstones/capstone-a-256-gpu-training-cluster/) · [B. Network telemetry and troubleshooting](capstones/capstone-b-network-telemetry-troubleshooting/) · [C. Distributed training performance](capstones/capstone-c-distributed-training-performance/) · [D. LLM inference platform](capstones/capstone-d-llm-inference-platform/) · [E. Fleet lifecycle automation](capstones/capstone-e-fleet-lifecycle-automation/) · [F. Reliability game day](capstones/capstone-f-reliability-game-day/) · [G. Fault-tolerant 512-node training](capstones/capstone-g-fault-tolerant-512-node-training/) · [H. Disaggregated LLM serving](capstones/capstone-h-disaggregated-llm-serving/) |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/validate_labs.py                          # verify every lab
cd book/part-1-foundations/ch03-linux-host-systems-diagnostics/lab
python check.py                                          # your progress on the starter code
```

## Realism boundary

Core labs run on a laptop (Level 1). A laptop or simulation **cannot** validate production RDMA
behaviour, real InfiniBand/RoCE congestion, GPU-to-NIC locality, NVLink/NVSwitch performance, switch
ASIC queue behaviour, or multi-node GPU scaling. Every simulated or modeled result in this book is
labelled as such; Level-2 and Level-3 extensions give the exact procedure for hardware-backed
validation.
