# Chapter 3 — Linux, Host Systems, and Performance Diagnostics

**Part I — Foundations · Course week 2 · Progressive Lab 1 (host discovery)**

A GPU server is still a Linux computer, and in synchronous training the slowest host sets the pace for
the whole cluster. This chapter teaches how the kernel sees an ORION `HX8` node: sockets, NUMA nodes,
PCIe links, interrupt vectors and block devices. It shows how to find host-side bottlenecks from
evidence: `lscpu`, `numactl`, `free`, `vmstat`, `iostat`, `mpstat`, `/proc/interrupts`, `ip`, `ethtool`,
`lspci`, `numastat` and the kernel log. It covers which numbers mislead (since-boot averages, diluted
`%iowait`, NVMe `%util`, idle PCIe downshift), how to price a host fault in cluster GPU-hours, and how to
build a safe, read-only collector and a baseline-driven analyzer for fleet-wide triage.

## Learning objectives

1. **Explain** how Linux scheduling, memory placement, block I/O, and interrupt handling map onto the
   NUMA and PCIe topology of a two-socket, eight-GPU server.
2. **Build** a host inventory with `lscpu`, `numactl`, `free`, `lspci`, `ip`, and `ethtool`, and
   **interpret** every field you record.
3. **Diagnose** CPU, memory, NUMA, storage, interrupt, and PCIe constraints from `vmstat`, `iostat`,
   `mpstat`, `/proc/interrupts`, `numastat`, and kernel-log evidence.
4. **Calculate** the bandwidth and cluster-level cost of a degraded PCIe link, NUMA-remote placement,
   and a single straggler node on ORION.
5. **Distinguish** benign signals from faults: since-boot averages, diluted `%iowait`, NVMe `%util`,
   idle PCIe link downshift, and isolated corrected errors.
6. **Design** a read-only diagnostic collector that degrades gracefully without root or on non-Linux
   platforms, and an analyzer that compares hosts against a baseline.
7. **Apply** the diagnostic loop to a "CPU utilization is low but throughput is poor" case and
   **validate** the fix with repeatable measurements.

## Prerequisites

Linux command line, Python, and basic IP networking. You should have read [Chapter 1](../ch01-ai-infrastructure-landscape/)
(workload types, scale-up and scale-out) and [Chapter 2](../ch02-anatomy-of-an-ai-data-center/)
(the `HX8` node and ORION racks). No CUDA, RDMA or ML background is required.

## Time budget

| Activity | Estimate |
|---|---|
| Reading the manuscript | 3–3.5 h |
| Exercises (knowledge checks, worked problems, case, design) | 4–5 h |
| Lab at L1 (collector, parsers, analyzer, written report) | 6–8 h |
| Optional L2/L3 extension on real hosts | 2–4 h |

## Lab tier

**L1** (laptop, < 60 s, no root, deterministic synthetic snapshots of six ORION nodes). Extensions:
**L2** (one real Linux/GPU host, root and non-root) and **L3** (≥ 2 RDMA-connected GPU nodes under an
`all_reduce_perf` load).

## Deliverable (course outline)

**A reusable host diagnostic script and a troubleshooting report**: `host_collector.py` and
`host_analyzer.py` passing `lab/check.py`, the "CPU low but throughput poor" report for `orion-n12`
(Exercise 3.8), and a fleet triage memo. Course week 2 deliverable: *host diagnostic runbook and
baseline*. The runbook excerpt (RB-HOST-03) and `lab/data/orion_hx8_baseline.yaml` are the starting
points.

## File map

```text
ch03-linux-host-systems-diagnostics/
├── README.md                     this chapter card
├── manuscript.md                 chapter text (§3.1–3.13, trade-offs, runbook, further reading)
├── exercises.md                  Exercises 3.1–3.17 + chapter deliverable
├── lab/
│   ├── README.md                 lab guide, severity policy, rubric, L2/L3 extensions
│   ├── manifest.yaml             environment manifest
│   ├── check.py                  python check.py [--impl starter|solution]
│   ├── data/
│   │   ├── snapshots/*.json      six hostdiag/1 snapshots (orion-n01, -07, -12, -19, -23, -28)
│   │   └── orion_hx8_baseline.yaml   expected HX8 configuration + thresholds
│   ├── tools/generate_snapshots.py   seeded generator (INSTRUCTOR ONLY; stripped from student release)
│   └── starter/
│       ├── host_collector.py     read-only collector (TODOs)
│       └── host_analyzer.py      parsers + fleet analyzer (TODOs)
├── solutions/                    INSTRUCTOR ONLY
│   ├── exercises-key.md          answers, marking guidance, planted-anomaly table
│   └── lab/host_collector.py, host_analyzer.py   reference implementations
└── review/REVIEW.md              editorial review log
```

## Where this chapter leads

Chapter 5 (GPU↔NIC topology mapping extends Lab 1), Chapter 14 (storage path), Chapter 16 (the
collector becomes a node-acceptance gate), Chapters 18–19 (kernel-log taxonomy for incident and fault
isolation), Chapter 20 (baseline changes as safe change), and Capstones A, E, F and G.
