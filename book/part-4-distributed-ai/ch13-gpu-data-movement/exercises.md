# Chapter 13 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/simulation, L2 single GPU
host, L3 multi-node GPU + RDMA. Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]`, or
`[ILLUSTRATIVE]`.

**Chapter deliverable (course outline):** *annotated data-path diagram and cross-layer diagnosis* —
Exercise 13.9 (O1) diagram plus Exercise 13.10 (O2) / lab diagnosis.

---

## Knowledge checks

**13.1 ★ L1.** Why does NVLink carry roughly 120× more bytes per GPU per step than the NIC for W-TRAIN
on ORION? *Evidence required:* the two volumes from Table 13.1 and the parallelism responsible.

**13.2 ★ L1.** List the four prerequisites for GPUDirect RDMA and explain why installing them does not
prove it is active. *Evidence required:* four items and one sentence on proof.

**13.3 ★ L1.** What do the topology labels PIX, PXB, PHB, and SYS mean for a GPU↔NIC pair, and which
of them does NCCL use GPUDirect RDMA for by default? *Evidence required:* four definitions; answer
labelled `[VENDOR-SPEC]`.

**13.4 ★★ L1.** Explain why `utilization.gpu` stays near 100 % on a rank that is waiting for a
straggler, and name two better metrics. *Evidence required:* mechanism + two metrics.

**13.5 ★ L1.** What limits how much of the DP gradient reduction can be overlapped with compute when
pipeline parallelism and gradient accumulation are used? *Evidence required:* the window and its
W-TRAIN value with arithmetic.

**13.6 ★★ L1.** Why is "eight NICs on eight different nodes started retransmitting at the same step"
evidence against eight independent NIC failures? Which component do you suspect?
*Evidence required:* probability argument (one sentence) and the component.

## Worked problems

**13.7 ★★ L1 — One pipeline message, two paths.** For one 8.39 MB (M/t = 67.1 MB / 8) pipeline
activation message between two ORION nodes, count host-DRAM copies, PCIe transfers, and total PCIe
bytes with and without GPUDirect RDMA. Estimate the transfer time with GPUDirect RDMA (45 GB/s
effective NIC) and an upper bound without it if staging is not pipelined (50 GB/s per copy).
*Evidence required:* a two-row table and both times with arithmetic.

**13.8 ★★ L1 — Amplification.** (a) If each rank independently has a 0.05 % chance of a slow step,
what fraction of steps contain at least one slow rank at N = 256, 1,024, and 4,096? (b) In a 64-rank
job, one rank's compute is 774 ms while the others take 600 ms; steps take 924 ms. Compute the GPU
time lost per step and the lost fraction.
*Evidence required:* three probabilities and two numbers, formulas shown.

## Outline-mandated exercises

**13.9 (O1) ★★ L1 — Trace a communication path.** Draw (Mermaid or ASCII) the path of a data-parallel
gradient chunk from GPU 6 on `orion-n05` to GPU 6 on `orion-n14`, annotating every hop (HBM, NCCL
buffer, PCIe switch, NIC, leaf name, NIC, PCIe switch, HBM) with its bandwidth class and an
illustrative latency. Draw it twice: with GPUDirect RDMA, and host-staged. Then show what changes if
the destination is GPU 2 on `orion-n14` (cross-rail).
*Evidence required:* two or three captioned diagrams, a copy/crossing count per variant, and the
canonical leaf/spine names used.

**13.10 (O2) ★★★ L1 — GPU utilization low, network utilization high.** Using the lab bundle (or the
windows in Section 13.13 if you have not finished the lab), determine whether communication,
synchronization, or data imbalance is responsible for the slowdown — for each of steps 0–19, 20–29,
and 30–59 — and justify each conclusion with at least two independent telemetry fields. State which
popular metric would have misled you and why.
*Evidence required:* a per-window verdict table with evidence fields, the decoy rejected, and the
misleading metric explained.

**13.11 (O3) ★★ L2/L3 — Validate GPUDirect RDMA and GPU/NIC locality.** Propose a measurement plan
for a supported two-node platform: the checks (configuration and performance), exact commands, what
result passes or fails, repetitions, and what to record. Include a deliberately misaligned GPU/NIC
test and a GDR-off control. Mark vendor-specific items.
*Evidence required:* a plan table with ≥ 8 rows (question, command, pass criterion, record), and a
safety note.

## Hands-on lab

**13.12 ★★ L1 — Cross-layer straggler diagnosis (lab).** Complete [lab/README.md](lab/README.md) so
that `python lab/check.py` passes and write the diagnosis report.
*Evidence required:* checker output (10/10 PASS), findings table (cause, ranks, onset, evidence,
owner, fix, validation), amplification numbers, and the annotated diagram from 13.9.

## Troubleshooting case

**13.13 ★★★ L1 — One slow node in a TP job.** A W-TRAIN-shaped job (TP 8) slows by 12 %. Per-rank
logs show that all eight ranks on `orion-n09` have TP communication time 3× the median; their compute,
clocks, and tokens are normal; DP and PP times are normal everywhere; the node was rebooted for a
driver update the previous evening. Rank hypotheses, name discriminating tests (commands and expected
output), give the most likely root cause, the safe fix, and validation evidence.
*Evidence required:* ≥ 3 ranked hypotheses, tests, root cause, fix, validation.

## Design challenge

**13.14 ★★★ L1 — Straggler telemetry for ORION-XL.** Design the per-rank telemetry pipeline for a
4,096-GPU job: which fields, sampling interval, how arrival skew is measured without synchronized
clocks, the join keys to hardware, the data volume per day, and the alert rules (with thresholds and
statistics). Defend one trade-off between fidelity and overhead.
*Evidence required:* field list, volume estimate with arithmetic, alert rules, and a defence paragraph.

## Reflection

**13.15 ★ L1.** Why is "the network is busy" not evidence that the network is the bottleneck?

**13.16 ★★ L1.** The lab shows that fixing rank 37 alone would not reduce step time. What does this imply
for how you validate a fix?

**13.17 ★★ L1.** Name three properties of real telemetry that the simulated bundle lacks, and how each
would complicate the diagnosis.

**13.18 ★ L1.** Which locality mistakes would *not* show up on an idle benchmark but would show up in
production? Why?
