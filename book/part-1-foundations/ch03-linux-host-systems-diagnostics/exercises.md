# Chapter 3 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: **L1** laptop/simulation ·
**L2** one real Linux (GPU) host · **L3** multi-node GPU + RDMA. Every exercise states the evidence
required for grading. Use ORION values from `docs/REFERENCE_CLUSTER.md` unless an exercise varies
one, and label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.

Course-outline mandated exercises are marked **(Outline)**. The chapter deliverable is at the end.

---

## Knowledge checks

### Exercise 3.1 — Reading the CPU map ★ · L1
On an `HX8`, `lscpu` reports `NUMA node0 CPU(s): 0-55,112-167`. (a) Which logical CPUs are SMT
siblings of physical cores on socket 1? (b) A launcher binds rank 2 (GPU 2) with `taskset -c 56-63`.
What is wrong with that, given Figure 3.1?
*Evidence required:* CPU lists, and one sentence that names the socket of GPU 2 and the consequence.

### Exercise 3.2 — Since-boot samples ★ · L1
Explain why the first line of `vmstat 1 5` and the first report of `iostat -x 1 2` must be discarded.
Give one example where including them would hide a real problem.
*Evidence required:* a definition of what the first sample measures, plus a numeric example.

### Exercise 3.3 — Diluted signals ★ · L1
A 224-CPU host shows `%iowait` = 4.5 % and a load average of 12 while 92 % idle. (a) What is the largest
number of blocked tasks consistent with that `%iowait`? (b) Which two undiluted metrics would you
check next?
*Evidence required:* the arithmetic, and the two metrics with the command that shows each.

### Exercise 3.4 — PCIe status lines ★ · L1
Classify each as *fault*, *probably benign — verify*, or *healthy*, and justify:
(a) GPU `LnkCap 32GT/s x16`, `LnkSta 32GT/s x8`, utilization 95 %;
(b) GPU `LnkCap 32GT/s x16`, `LnkSta 2.5GT/s x16`, utilization 0 %;
(c) BMC VGA `LnkCap 5GT/s x1`, `LnkSta 5GT/s x1`;
(d) rail NIC `LnkCap 32GT/s x16`, `LnkSta 16GT/s x16`, captured during an all-reduce benchmark.
*Evidence required:* a verdict per line, with the rule applied.

### Exercise 3.5 — Corrected versus uncorrected ★ · L1
Contrast PCIe AER *corrected*, *uncorrected non-fatal* and *uncorrected fatal* errors, and EDAC CE
versus UE. For each, say whether the alert rule should be based on rate or on presence.
*Evidence required:* a table with five rows: event, consequence, rule type, suggested first action.

### Exercise 3.6 — NUMA and utilization ★★ · L1
Why does NUMA-remote memory placement seldom show up as low CPU utilization? Name the measurement
that does reveal it, and the command you would use for a running PID.
*Evidence required:* a mechanism explanation, plus the exact `perf stat` and `numastat` invocations.

### Exercise 3.7 — Safe collection ★ · L1
List four properties that make a diagnostic collector safe to run on a production training node. For
each, give a concrete example of a command or argument it would refuse or handle.
*Evidence required:* four properties, each with one example.

---

## Troubleshooting case

### Exercise 3.8 — CPU utilization is low but throughput is poor ★★ · L1 **(Outline)**
Snapshot `lab/data/snapshots/orion-n12.json` comes from a node running *W-MM*, an image–text
fine-tuning job. This is a variation on ORION's reference workloads: its training shards are read
from the node-local NVMe array `md0`, and each W-MM job runs on a single node (8 GPUs), so a slow node
slows only its own job. Samples per second on this node are about 40 % below its peers,
and the operator's note says "CPU utilisation is low".

1. From the snapshot alone, list every abnormal signal with its evidence: the section and the value.
2. Form **at least four hypotheses** that involve memory locality, I/O wait, interrupts, PCIe
   constraints or CPU frequency, and rank them by how well each explains a ~40 % throughput loss.
3. For each hypothesis, give one **discriminating test** that you would run next on the live host (L2),
   and the result that would confirm or reject it.
4. State the most likely primary cause, the contributing factors, and the **order** of remediation.
   Each change must be safe (drained node, change process).
5. Define the measurement that would validate the fix: the metric, warm-up, repetitions and the
   statistic you would report.

*Evidence required:* a one-page report. It needs a signal table with section, value and baseline, a
ranked hypothesis table with tests, the root-cause statement, a remediation order and a validation
plan. Quote at least three raw lines from the snapshot.

---

## Worked problems

### Exercise 3.9 — The price of a narrower pipe ★★ · L1
Using the method of §3.11 and W-TRAIN's parallelism (TP = 8, PP = 4, DP = 8, BF16 gradients, ring
all-reduce, 45 GB/s achievable on a healthy rail, 82 % PCIe efficiency):
(a) Compute the raw per-direction bandwidth of PCIe Gen5 x16, Gen4 x16, Gen4 x2 and Gen1 x16 (note that
Gen1/Gen2 use 8b/10b encoding).
(b) Rail NIC 4 on one node has trained at Gen4 x16 instead of Gen5 x16. Compute the extra DP all-reduce
time per step (upper bound) and the GPU-hours lost per day across ORION.
(c) ORION-256 has no spare node. Using the decision rule of §3.11 Step 6, decide whether to keep
running, shrink to DP = 7, or plan a stop for this fault, and compare with the Gen3 x8 case.
*Evidence required:* formulas, substituted values and results with units, each labelled `[MODELED]`.

### Exercise 3.10 — Queues, stripes and packets ★★ · L1
Use the live `iostat` report in the `orion-n12` snapshot.
(a) Verify the `aqu-sz` of `nvme3n1` and of `md0` with Little's law.
(b) Compute `md0`'s delivered read throughput in MB/s (SI), from `r/s` and `rareq-sz`.
(c) The loader keeps about 41 requests of 512 KiB outstanding against `md0`. If `nvme3n1` behaved like
its siblings, so that array latency fell to about 0.25 ms, what throughput would the concurrency allow,
and what would then become the limit?
(d) Show that the snapshot's `%iowait` is consistent with the `vmstat b` value.
(e) Compute the frontend packet rate at 200 Gb/s for MTU 9000 and MTU 1500, and the ratio between them.
*Evidence required:* every formula with substituted values; one sentence of interpretation per part.

---

## Hands-on lab

### Exercise 3.11 — Host collector and fleet analyzer (Lab 3, Progressive Lab 1) ★★★ · L1 (L2/L3 extensions) **(Outline)**
Complete [`lab/README.md`](lab/README.md) Parts A–D: a **Python script that collects selected host
metrics and produces a timestamped report** (`host_collector.py`), and an analyzer that triages six ORION
snapshots against the HX8 baseline.
*Evidence required:* `python check.py` output showing 21/21 PASS; the generated `fleet_report.md`; the
written report for Exercise 3.8; and the fleet triage memo (lab Part D.3).

### Exercise 3.12 — Host inventory and diagnostic snapshot ★ · L1, L2 **(Outline)**
Use `lscpu`, `numactl`, `free`, `vmstat`, `iostat`, `ip`, `ethtool`, `lspci` and `dmesg` to build a
**host inventory and diagnostic snapshot**.
- **L1 path:** from `orion-n01.json` (the reference node), produce a one-page inventory table: CPU
  model and topology, NUMA nodes with CPU lists and memory, GPU and NIC BDFs with NUMA node and link
  state, interface names with MTU and speed, NVMe devices, kernel and driver versions visible in the
  snapshot. Mark each value with the section it came from.
- **L2 path:** run your collector on a Linux host you are authorized to inspect (a workstation or cloud
  VM is fine), once as an unprivileged user and once as root if permitted. Produce the same table and
  list which fields were missing without root and which unprivileged fallback (if any) recovered them.
*Evidence required:* the inventory table with provenance per value; for L2, both raw JSON snapshots
and the gap comparison.

---

## Design challenge

### Exercise 3.13 — Host health at ORION-XL scale ★★★ · L1
ORION-XL has 512 `HX8` nodes. Design the host-diagnostics strategy that Fleet, SRE and Training Infra
will share. Decide and defend: (a) what runs continuously (agents, metrics, intervals) and what runs
on demand (the collector), with the trigger for each; (b) privilege model (root or not, where, audited
how); (c) which analyzer findings drain a node automatically and which only page a human, with the
rationale in terms of false-positive cost and lost GPU-hours; (d) storage and retention of snapshots
(estimate the volume of one full-fleet sweep using the size of the supplied snapshots); (e) how the
baseline YAML is versioned and changed safely.
*Evidence required:* a design note of no more than two pages with a decision table, the
snapshot-volume arithmetic, and at least two explicitly rejected alternatives with reasons.

---

## Reflection and review

### Exercise 3.14 ★ · L1
The lab's snapshots are `[SIMULATED]`. List three things your analyzer could get wrong on real hosts that
the simulated data cannot reveal, and how you would find out.
*Evidence required:* three items, each with a validation step.

### Exercise 3.15 ★ · L1
Your analyzer reports `orion-n28` as "healthy (check gaps)". What exactly can and cannot be
concluded about that node, and what would you collect next?
*Evidence required:* a list of the missing evidence, with the command or privilege needed for each.

### Exercise 3.16 ★★ · L1
The §3.11 cost estimate is an upper bound. Name the assumptions that make it an upper bound, and
describe the L3 measurement that would replace it with a measured value.
*Evidence required:* at least three assumptions and a measurement plan (tools, repetitions, statistic).

### Exercise 3.17 ★★ · L1
Choose one threshold in `orion_hx8_baseline.yaml`. Argue for a tighter and for a looser value, and say
what fleet data you would need to set it from evidence rather than judgment.
*Evidence required:* both arguments and a data requirement.

---

## Chapter deliverable (Outline)

**A reusable host diagnostic script and a troubleshooting report.** Submit:

1. `host_collector.py` and `host_analyzer.py` passing `python check.py` (21/21). Include your
   `manifest.yaml`, filled in for any L2/L3 run.
2. The troubleshooting report for `orion-n12` (Exercise 3.8).
3. The fleet triage memo (lab Part D.3) and the inventory from Exercise 3.12.

Grading follows the lab rubric (100 points) in `lab/README.md`, §8.
