# Chapter 12 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/simulation, L2 single
GPU host, L3 multi-node GPU + RDMA. Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]`, or
`[ILLUSTRATIVE]`. Lab data lives in [lab/data/](lab/data/).

**Chapter deliverable (course outline):** *collective benchmark report with scaling and bottleneck
analysis* — Exercises 12.11 (O2) and 12.12 (O3) plus the lab report, assembled as in Section 12.11.
This is also the week-9 submission for **Progressive Lab 5**.

---

## Knowledge checks

**12.1 ★ L1.** State the contract of reduce-scatter and of all-gather, and show that composing them
yields all-reduce. *Evidence required:* two definitions and a 2-rank example.

**12.2 ★ L1.** Why is all-to-all harder on a network than all-reduce of the same per-rank size, even
though each rank sends fewer bytes? *Evidence required:* two mechanisms (fan-out/incast, cross-rail
paths, data dependence).

**12.3 ★ L1.** Give the nccl-tests busbw correction factor for all-reduce, all-gather, reduce-scatter,
broadcast, and all-to-all on n = 16 ranks. *Evidence required:* five numbers.

**12.4 ★ L1.** Explain the payload efficiency and latency trade-off among NCCL's LL, LL128, and Simple
protocols. *Evidence required:* a three-row comparison with the reason each costs what it costs.

**12.5 ★★ L1.** What is an NCCL channel, and why can a 16-rank all-reduce across two HX8 nodes reach
≈ 350 GB/s busbw when each NIC is 50 GB/s? *Evidence required:* explanation with the 8 × 50 GB/s
arithmetic.

**12.6 ★ L1.** For each of `NCCL_DEBUG`, `NCCL_DEBUG_SUBSYS`, `NCCL_IB_HCA`, `NCCL_SOCKET_IFNAME`,
`NCCL_ALGO`, `NCCL_PROTO`, `NCCL_TOPO_DUMP_FILE`, and `NCCL_IB_GID_INDEX`, state what it controls and
whether you would set it in a production job template. *Evidence required:* an eight-row table.

**12.7 ★★ L1.** In a home-made PyTorch benchmark, an engineer reports 2,000 GB/s busbw for an 8-GPU
all-reduce. Name the most likely measurement bug and the fix. *Evidence required:* bug, fix, and why.

## Worked problems

**12.8 ★★ L1 — From rows to bandwidth.** From `lab/data/c4_4node_aligned.log`, take the rows for
1 MiB, 64 MiB, and 4 GiB (out-of-place). Recompute algbw and busbw by hand, state the region each row
is in, and compare the 4 GiB busbw with the node's NIC egress limit. *Evidence required:* nine
computed values with arithmetic, region labels, and an efficiency percentage.

**12.9 ★★ L1 — Buckets and the alpha-beta model.** For a 64-rank all-reduce with α = 47 µs and
B = 346 GB/s (busbw), compute: (a) the time for 4 MB, 25 MB, and 256 MB; (b) n½; (c) the total time to
reduce 4.375 GB as 25 MB buckets versus one message, and explain the difference in terms of α.
*Evidence required:* all values with formulas.

## Outline-mandated exercises

**12.10 (O1) ★ L1 — Collectives by hand.** Three ranks hold R0 = [2, 4, 6], R1 = [1, 3, 5],
R2 = [10, 20, 30]. Give the result on every rank of: all-reduce (sum), reduce (sum, root R0),
reduce-scatter (sum; rank *r* keeps element *r*), all-gather (of each rank's first element),
broadcast (root R1), and all-to-all. Then trace a ring all-reduce for this example step by step and
count the bytes each rank sends, assuming 4-byte elements.
*Evidence required:* six results, a step table with 2(n − 1) = 4 steps, and the byte count compared
with 2(n − 1)/n × S.

**12.11 (O2) ★★ L1 — Analyze an NCCL result set across message sizes.** Using your lab
implementation (or by hand), analyze all six configurations in `lab/data/`. For each, identify the
latency-dominated and bandwidth-dominated regions (size ranges), fit α and B, compute n½, and state
the plateau busbw. Then write the scaling analysis: how plateau busbw and α change from 1 to 8 nodes,
and what that says about the fabric.
*Evidence required:* a summary table (six rows), region boundaries, a log-log plot of time vs size
for c2 and c5 (matplotlib), and a 150-word scaling verdict.

**12.12 (O3) ★★★ L1 — Two rank mappings.** Compare c2 (aligned) and c3 (alternative map). (a) Before
looking at the plateau, *predict* the plateau busbw of each from the topology (number of NICs used,
GPU↔NIC path type, GPUDirect RDMA on or off), with arithmetic. (b) Compare with the data. (c) List the
topology information you would need to *prove* the hypothesis on real hardware, the exact command or
log line for each item, and what result would falsify your hypothesis.
*Evidence required:* the prediction with arithmetic, the comparison, and an evidence table of at
least five items (artifact, command, expected result if hypothesis true, result that falsifies it).

## Hands-on lab

**12.13 ★★ L1 — nccl-tests analysis toolkit (lab).** Complete [lab/README.md](lab/README.md) tasks 1–6
so that `python lab/check.py` passes. Optional: run `lab/optional/gloo_allreduce.py` on your laptop if
PyTorch is installed and parse your own output.
*Evidence required:* checker output (10/10 PASS), summary table, anomaly labels with explanations,
and (optional) your gloo log labelled `[MEASURED]` with the environment.

## Troubleshooting case

**12.14 ★★★ L1 — Latency doubled, bandwidth fine.** After a container image update, the nightly
8-node run shows: 8 B all-reduce time 95 µs (baseline 47 µs); 1 MiB time 118 µs (baseline 53 µs);
plateau busbw 344 GB/s (baseline 345). `#wrong` = 0. No node changes. Rank hypotheses, name
discriminating tests (with commands and the log lines you expect), give the most likely root cause, the
safe fix, and the validation evidence.
*Evidence required:* ≥ 3 ranked hypotheses, tests with expected outcomes, root cause, fix, and
validation criteria.

## Design challenge

**12.15 ★★★ L1 — ORION collective acceptance suite.** Design the nccl-tests acceptance suite that
Fleet runs before a node joins the training partition and nightly on idle nodes. Cover: which
collectives, which communicator shapes (single node, two-node pairs, rail-pinned one-GPU-per-node,
full 8-node), size ranges, repetitions, pass/fail thresholds with the statistic used, run time budget,
artifacts recorded, and safety constraints. Defend one trade-off (coverage vs time vs fabric impact).
*Evidence required:* the suite as a table, thresholds tied to Table 12.7 baselines, and a
one-paragraph defence.

## Reflection

**12.16 ★ L1.** Why is nccl-tests "Avg bus bandwidth" a poor single-number summary? What two numbers
would you report instead?

**12.17 ★★ L1.** The lab's data are simulated from an alpha-beta model. Name three real NCCL behaviours
the simulation cannot show and how each would appear in a real sweep.

**12.18 ★★ L1.** A benchmark on an idle fabric shows rail misalignment costs only 3 %. Why might the
same misalignment cost much more in production?

**12.19 ★ L1.** What would you need to add to a single nccl-tests log before you would accept it as
evidence in an incident review?
