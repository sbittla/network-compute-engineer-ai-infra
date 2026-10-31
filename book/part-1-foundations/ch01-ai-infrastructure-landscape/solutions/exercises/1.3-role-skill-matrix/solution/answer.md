# 1.3 — Role-to-skill matrix: model answer

Reference: manuscript Section 1.8, Table 1.10 (author judgment `[ILLUSTRATIVE]`, not survey data). The
0–3 scale: 0 not required, 1 awareness, 2 working, 3 expert. Accept ±1 per cell when the learner
justifies it.

## Matrix (14 domains), with a worked personal column

The "Me" column is an example for a learner who is a data-center network engineer targeting **AI Network
Engineer**; each learner's column is their own.

| Skill domain | AI Network Engineer | GPU Cluster Engineer | AI Infrastructure SRE | Me (example) |
|---|:-:|:-:|:-:|:-:|
| AI data-center architecture, power, cooling | 2 | 2 | 1 | 1 |
| Linux host: CPU, memory, NUMA, PCIe, drivers | 1 | 3 | 2 | 1 |
| GPU architecture, CUDA execution, profiling | 1 | 2 | 1 | 0 |
| NVLink/NVSwitch, GPU↔NIC topology | 2 | 3 | 1 | 0 |
| L2/L3, BGP, ECMP, leaf-spine | 3 | 1 | 1 | 3 |
| RDMA, RoCEv2, InfiniBand, congestion control | 3 | 2 | 1 | 1 |
| Switches, optics, cabling, physical layer | 3 | 1 | 1 | 2 |
| NCCL and collective communication | 2 | 3 | 1 | 0 |
| Bare-metal provisioning, firmware lifecycle | 1 | 3 | 2 | 1 |
| Kubernetes and Slurm scheduling | 1 | 2 | 2 | 0 |
| Storage, data pipelines, checkpointing | 1 | 2 | 2 | 1 |
| Observability, SLOs, incident response | 2 | 2 | 3 | 2 |
| Automation (Python, IaC), safe change | 2 | 2 | 3 | 2 |
| Capacity and cost modeling | 1 | 2 | 2 | 1 |

## Justifications (two highest, two lowest per role)

- **AI Network Engineer, high:** L2/L3 and BGP (3), because the rail-optimized fabric is an eBGP
  leaf-spine they must design and debug; RDMA and congestion control (3), because RoCEv2 collectives fail
  on PFC/ECN mistakes no one else can diagnose. **Low:** Linux host (1) and bare-metal provisioning (1),
  because they need only enough to hand off to Fleet when the fault is host-side.
- **GPU Cluster Engineer, high:** Linux host/PCIe/NUMA (3), because GPU↔NIC affinity and link training
  decide per-node performance; NCCL (3), because they validate collectives on every node they deliver.
  **Low:** L2/L3/BGP (1) and physical layer (1), because Fabric owns routing and optics.
- **AI Infrastructure SRE, high:** observability and incident response (3), because SLOs and on-call are
  the job; automation and safe change (3), because remediation at fleet scale must be scripted and
  reversible. **Low:** GPU architecture (1) and L2/L3 (1), because they consume those signals rather
  than design those systems.

Check against the chapter: every role is ≥ 2 on observability, every role has a 3 somewhere, and none
is 3 everywhere.

## Gap list (cells where Me ≤ target − 2)

| Domain | Target / me | Chapter(s) | Artifact that closes the gap |
|---|---|---|---|
| RDMA, RoCEv2, congestion control | 3 / 1 | 8, 9 | Chapter 9 lab output: PFC/ECN telemetry analysis with a written diagnosis |
| NVLink, GPU↔NIC topology | 2 / 0 | 5 | Chapter 5 lab: topology map from `nvidia-smi topo -m` and a rank-placement table |
| NCCL and collectives | 2 / 0 | 12, 13 | `all_reduce_perf` result table with bus-bandwidth interpretation (Chapter 12 lab) |

A full-credit gap list names a chapter and a concrete, checkable artifact for every gap; "read more about
RDMA" earns no credit.

**Common wrong answers:** rating everything 3; listing tools ("Wireshark", "Ansible") instead of skill
domains; claiming "the market requires X" without the dated register of Section 1.8 (Exercise R2).
