# Chapter 8 — RDMA, RoCEv2, and InfiniBand

**Part III — Networking for AI Clusters · Course week 5**

Remote Direct Memory Access (RDMA) moves data between registered application buffers on two hosts
without kernel copies, system calls, interrupts, or — for one-sided operations — the remote CPU. This
chapter explains the verbs model (queue pairs, memory registration, completion queues), the RoCEv2
encapsulation and InfiniBand fabric management that carry it, how its reliable transport behaves under
loss (go-back-N, ACK timeouts, retry budgets), how to design a multi-rail attachment for an 8-NIC GPU
server, and how to prove a fabric is ready before it carries a training job. The lab builds an RDMA
deployment-readiness validator and a perftest analyzer on synthetic captures from eight ORION nodes
with planted faults.

## Learning objectives

1. **Explain** the RDMA verbs model (PDs, MRs with `lkey`/`rkey`, RC/UC/UD queue pairs, CQs, the QP
   state machine) and distinguish one-sided (READ/WRITE) from two-sided (SEND/RECV) operations.
2. **Draw and compare** the data path of a message sent over TCP sockets and over RDMA, counting CPU
   copies, interrupts, system calls, and context switches on each side.
3. **Decode** a RoCEv2 packet (Ethernet, IP with DSCP/ECN, UDP port 4791, Base Transport Header) and
   **calculate** wire efficiency, packet rate, and payload ceiling for a given path MTU.
4. **Describe** InfiniBand management (LIDs, subnet manager, P_Keys, SL/VL, credit-based flow control)
   and **compare** RoCEv2 and InfiniBand across transport, management, operations, and evidence.
5. **Calculate** the cost of packet loss under go-back-N recovery and the retry time budget set by the
   ACK timeout and retry count.
6. **Design** a multi-rail RDMA attachment (addressing, GID selection, QoS marking, GPU/NIC locality)
   for an 8-NIC GPU server.
7. **Validate** RDMA deployment readiness with real tools and a scripted checklist, and **diagnose**
   underperforming pairs from perftest results.

## Prerequisites

- [Chapter 3](../../part-1-foundations/ch03-linux-host-systems-diagnostics/) — PCIe, NUMA, `ethtool`, `ip`.
- [Chapter 5](../../part-2-accelerated-compute/ch05-gpu-interconnects-host-topology/) — HX8 topology and GPU/NIC locality.
- [Chapter 7](../ch07-ethernet-datacenter-network-foundations/) — leaf-spine, ECMP, rail-optimized design, ORION addressing.

Leads to [Chapter 9](../ch09-congestion-control-lossless-fabrics/) (PFC/ECN/DCQCN),
[Chapter 10](../ch10-switches-optics-physical-layer/), [Chapter 12](../../part-4-distributed-ai/ch12-collective-communication-nccl/),
[Chapter 13](../../part-4-distributed-ai/ch13-gpu-data-movement/), and Capstones A, B, and H.

## Estimated time

| Activity | Time |
|---|---|
| Reading `manuscript.md` | 3.5–4 h |
| Exercises (`exercises.md`) | 4–5 h |
| Lab (L1) | 3–4 h |
| L3 extension (optional, hardware) | 3 h + lab-fabric access |

## Lab tiers

- **L1** (required): readiness validator + perftest analyzer on synthetic captures — `lab/`.
- **L3** (optional): real inventories and perftest runs on a dedicated RDMA lab fabric with a filled-in
  manifest — `lab/README.md` §8.

## Deliverable (course outline)

**RDMA design note and deployment-readiness checklist** — Exercises 8.11 (design note) and 8.12
(checklist), supported by the lab's generated readiness report and perftest diagnosis (Exercise 8.13).

## File map

```text
ch08-rdma-rocev2-infiniband/
├── README.md                     this chapter card
├── manuscript.md                 chapter text (~10,000 words)
├── exercises.md                  20 exercises incl. 3 outline-mandated + deliverable
├── lab/
│   ├── README.md                 lab guide, rubric, L3 extension
│   ├── manifest.yaml             environment manifest (L1; L3 fields to record)
│   ├── check.py                  checker: python check.py [--impl starter|solution]
│   ├── tools/generate_data.py    deterministic generator (seed 8) — instructor copy only (stripped from student release)
│   ├── data/                     baseline.yaml, inventory/ (8 nodes), perftest/ (64 runs + PCIe CSV)
│   └── starter/                  readiness.py, perftest_analysis.py (TODOs)
├── solutions/                    INSTRUCTOR ONLY
│   ├── exercises-key.md          worked answers and marking guidance
│   └── lab/                      reference implementation + PLANTED_FAULTS.md
└── review/REVIEW.md              editorial review log
```
