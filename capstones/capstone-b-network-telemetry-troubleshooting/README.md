# Capstone B: Build an AI Network Troubleshooting and Telemetry System

You will build the system that tells Halcyon AI's Fabric on-call engineer, within a few polling
intervals, which device on the ORION-256 RoCEv2 backend is causing trouble. The system tells them
what kind of trouble it is and what evidence proves it. It also stays silent for planned maintenance,
benign synchronized bursts, counter wraps and counter resets. The deliverable is the working pipeline
plus the operational artifacts that make it usable: telemetry schema, parser, report or dashboard,
alert rules, runbook, injected-fault scenarios, a false-positive analysis and an incident report.
On a real fabric, the difference between a monitoring system and a paging-noise generator is
almost entirely in the parts this capstone grades.

## Audience and prerequisites

**Audience (course outline, Section 16):** AI Network Engineer, Network Operations Engineer.

**Recommended preparation:** Chapters [7](../../book/part-3-networking/ch07-ethernet-datacenter-network-foundations/),
[8](../../book/part-3-networking/ch08-rdma-rocev2-infiniband/),
[9](../../book/part-3-networking/ch09-congestion-control-lossless-fabrics/),
[10](../../book/part-3-networking/ch10-switches-optics-physical-layer/) and
[18](../../book/part-5-production-operations/ch18-observability-slos-incident-response/). Chapters
[3](../../book/part-1-foundations/ch03-linux-host-systems-diagnostics/) (host counters) and
[20](../../book/part-5-production-operations/ch20-automation-safe-change/) (change calendars, safe change)
help with the runbook and the suppression logic.

## Scenario

ORION-256's backend is a rail-optimized, 2-tier RoCEv2 fabric: 8 rail leaves, 4 spines, and 32 HX8
hosts with eight 400 Gb/s NICs each ([REFERENCE_CLUSTER.md](../../docs/REFERENCE_CLUSTER.md) §2). RoCE
traffic rides DSCP 26 → traffic class 3, lossless with PFC and ECN. Over the last month, Training Infra
has opened four tickets that began "the job got slow and we think it's the network". Each took the
Fabric team more than an hour to confirm or refute. The existing alerting pages on every PFC counter
increment and is muted by most of the team.

You have a 30-minute capture of the whole backend on 2026-10-12, 10:00–10:30 UTC. W-TRAIN runs on the
default 24-node training partition (`orion-n01`–`n24`, TP 8 × PP 4 × DP 6, a declared variation of the
full 32-node run with the global batch set to 1,152 sequences, because 1,024 is not divisible by DP = 6), while `orion-n25`–`n32` serve inference. The capture is in
the three formats the fleet actually emits: CLI text from the leaf vendor, streaming JSON from the
spine vendor, and `ethtool -S` plus RDMA `hw_counters` from host agents. The capture also includes
the topology, the change calendar and the device profiles. Several faults were injected. Several
other events will look like faults.

## Problem statement

Design and build a telemetry pipeline and alerting system for the ORION backend that:

1. normalizes all three sources into one documented schema, with lineage to native counter names;
2. computes rates that are correct across 32-bit wraps, counter resets and jittered poll times;
3. raises **root-cause** alerts for each fault class (PFC storm, link degradation, ECN
   misconfiguration, ECMP imbalance, link down) with evidence in the alert text;
4. suppresses alerts for planned work on a device *or on its link peer*, and does not page on benign
   bursts or single-interval glitches;
5. demonstrates its precision and recall, and the latency cost of achieving them.

**Success criteria:** recall 1.0 and precision ≥ 0.9 on the supplied capture, scored by when each page
fires against the fault's onset window. With five injected faults, precision ≥ 0.9 means zero false
pages, and five positives cannot estimate a production false-positive rate. Also required: a quantified
persistence/threshold trade-off, and a runbook another engineer could follow at 3 a.m.

## Required artifacts

The first eight rows are the Capstone B artifacts from the course outline (Section 16). The remaining
rows are required of every capstone.

| Artifact | Template | Expected evidence label |
|---|---|---|
| Telemetry schema | [telemetry-schema.md](templates/telemetry-schema.md) | design |
| Parser or collector | `starter-kit/starter/telemetry.py` (your implementation) | code + checker output |
| Dashboards or report | [dashboard-report-spec.md](templates/dashboard-report-spec.md) | `[SIMULATED]` |
| Alert rules | [alert-rules.md](templates/alert-rules.md) | thresholds justified from data |
| Runbook | [runbook.md](templates/runbook.md) | procedure |
| Injected-fault scenarios | [injected-fault-scenarios.md](templates/injected-fault-scenarios.md) | `[SIMULATED]`; `[MEASURED]` if L3 |
| False-positive discussion | [false-positive-analysis.md](templates/false-positive-analysis.md) | `[SIMULATED]` |
| Incident report | [incident-report.md](templates/incident-report.md) | `[SIMULATED]` capture, stated |
| Problem statement; architecture; assumptions | [design-doc.md](templates/design-doc.md) §1–3, [assumptions-register.csv](templates/assumptions-register.csv) | |
| Implementation or simulation boundary | [design-doc.md](templates/design-doc.md) §4 | |
| Test plan; results | [test-plan.md](templates/test-plan.md), [results-table.csv](templates/results-table.csv) | `[SIMULATED]` and `[MEASURED]` kept apart |
| Failure analysis; security considerations | [design-doc.md](templates/design-doc.md) §8–9 | |
| Final engineering review | [final-engineering-review.md](templates/final-engineering-review.md) | |

## Milestones

| Milestone | Week | What you hand in |
|---|---|---|
| M0: choose | 8 | Capstone choice; read the bundle with `zcat`; list what you think is wrong before writing code |
| M1: proposal | 10 | Problem statement, schema v1, checks 01–05 passing |
| M2: pipeline | 12 | Rates and detection: checks 01–11 passing; rule spec v1 |
| M3: draft | 13 | All checks; false-positive analysis; runbook; incident report draft; your added scenario |
| M4: final | 14 | Complete pack, final engineering review, 15-minute presentation |

## Tier options

| Tier | Scope | What it adds |
|---|---|---|
| **L1 (required)** | [starter-kit](starter-kit/) on the supplied `[SIMULATED]` capture | Full marks are achievable at L1 |
| **L2 (optional)** | Parse real `ethtool -S` and RDMA hw_counters from one lab host | Confirms counter names and semantics on real drivers |
| **L3 (optional)** | Stream lab-switch counters, reproduce an incast and an ECN-disabled case, detect both | `[MEASURED]` detection latency, precision and recall |

**Advanced extension (course outline):** use streaming telemetry or lab switch counters and validate a
suspected congestion issue on physical hardware. The procedure is in the
[starter-kit README, Section 8](starter-kit/README.md#8-extensions-hardware-backed-validation-l2l3).

> **Realism boundary:** The capture is generated, not recorded. It reproduces counter signatures but
> not the control loops behind them: no PFC/ECN dynamics, no buffer occupancy, no telemetry loss. A
> threshold that is perfect on this capture is a hypothesis about production, not a result. Present
> it as such, and use the L3 extension or a production baseline to test it.

## How the chapters map to the artifacts

| Artifact | Chapters |
|---|---|
| Schema, parser (switch + NIC counters) | 3, 8, 10 |
| Alert rules (PFC, ECN, CNP, ECMP, FEC/FCS) | 7, 8, 9, 10 |
| Report/dashboard, false-positive analysis | 18, 22 |
| Runbook, incident report | 18, 19, 20 |
| Injected-fault scenarios | 9, 10, 19 |

## Grading

Graded with the [capstone rubric](../RUBRIC.md): pass at 70/100 with at least 50 % in both
*Architecture and technical correctness* and *Measurement and analysis*; distinction at 90/100 with
reproducible evidence. For Capstone B, excellent work looks like this:

| Dimension | What excellent looks like in Capstone B |
|---|---|
| Problem framing and assumptions (10) | Success criteria in on-call terms: precision, recall, latency, pages during changes. Poll intervals and counter widths are recorded as assumptions |
| Architecture and technical correctness (20) | Correct direction semantics for pause and ECN counters, correct wrap/reset policy, and root-cause attribution through the topology rather than symptom ports |
| Implementation / reproducibility (15) | All checks pass; unit tests for parsers and counter arithmetic; one command reproduces every table |
| Measurement and analysis (20) | Persistence and threshold sweeps, each threshold justified from baseline percentiles, detection latency per fault, simulated vs measured kept apart |
| Reliability, security and operations (15) | Runbook with read-only first steps and approvals, suppression that understands link peers, meta-monitoring of the collectors, least-privilege collection |
| Troubleshooting and engineering judgment (10) | The incident report separates proven cause from correlation and explains why the twenty symptomatic ports are not twenty incidents |
| Communication and portfolio quality (10) | A reader understands the dashboard in 30 seconds and can rerun the analysis in 30 minutes |

## File map

```text
capstone-b-network-telemetry-troubleshooting/
├── README.md            this brief
├── templates/           design doc, schema, alert rules, scenarios, FP analysis, runbook, incident report,
│                        dashboard/report spec, test plan, assumptions, results, final review
├── starter-kit/         L1 pipeline: data/ (capture), tools/ (instructor edition only), starter/telemetry.py, check.py, README.md
├── instructor/          grading guide, exemplar summary, reference implementation (removed in student edition)
└── review/REVIEW.md     editorial review log
```
