# Chapter 23 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/simulation, L2 single
GPU host, L3 multi-node GPU with RDMA. All ORION values are from
[REFERENCE_CLUSTER.md](../../../docs/REFERENCE_CLUSTER.md) and are `[ILLUSTRATIVE]` unless labelled.
Every exercise states the evidence required for grading.

## A. Knowledge checks

**K1 ★ L1.** List the five elements of a strong capstone problem statement and, for each, give one
consequence it lets a reviewer check.
*Evidence required:* five elements, five checkable consequences.

**K2 ★ L1.** Why does the assumptions register require an `owner` and a `validation` field for every
entry? What goes wrong in practice when either is missing?
*Evidence required:* one failure mode for each field.

**K3 ★ L1.** What is the purpose of an ADR's revisit trigger? Write a revisit trigger for ORION's
decision to keep TP = 8 inside the NVLink domain.
*Evidence required:* a trigger that is observable (a metric or event), not an opinion.

**K4 ★ L1.** Why must a rack power budget use maximum rather than sustained node power? Name two
operational events that drive a rack towards its maximum.
*Evidence required:* the reason plus two events.

**K5 ★★ L1.** On ORION, compare the blast radius of (a) a rack power failure and (b) a rail-leaf
failure, in GPUs lost and in jobs affected. Explain why they differ.
*Evidence required:* numbers for (a); a mechanism-based explanation for (b).

**K6 ★★ L1.** In FMEA, RPN = S × O × D. Why does a high D score increase priority, and why does that
favour investing in failure modes that "only make things slower"?
*Evidence required:* correct definition of D; one ORION example.

**K7 ★ L1.** Which of these may a capstone label `[MEASURED]` at tier L1: (a) linter runtime on a
laptop; (b) NCCL bus bandwidth from a model; (c) parse time of a 1 GB telemetry file;
(d) TTFT from a serving simulator? Give the correct label for each that may not.
*Evidence required:* four classifications with labels.

**K8 ★ L1.** What are the three valid outcomes of a design review, and why is "we'll take it
offline" not one?
*Evidence required:* three outcomes; one sentence on accountability.

## B. Worked problems

**W1 ★★ L1 — Repairing the Kestrel design.** Team Kestrel's bundle lists 34 HX8 nodes, 8 GPUs per
node, `total_gpus: 256`, no declared spares, workload parallelism TP = 8, PP = 4, DP = 16, rail
leaves of radix 64 with 34 downlinks and 32 uplinks (8 per spine, 4 spines), a claimed "1:1"
subscription, 512 backend cables, and 8 GPU racks with a usable budget of 45 kW each. The team says
two nodes are spares that must stay cabled to the backend so a failed node can be swapped without
recabling.

1. Fix the GPU accounting and the parallelism so that the design is internally consistent.
2. Show the leaf port arithmetic, then propose a leaf configuration that keeps both spares cabled,
   uses an equal number of uplinks to each spine, and fits radix 64. State the resulting
   oversubscription with and without the spares active, the spine port usage, and the backend cable
   count.
3. How many racks does a 34-node design need at 45 kW per rack? What are the options if the row has
   only 8 racks?

*Evidence required:* every formula with substituted values; final numbers with units.

**W2 ★★ L1 — Checkpoint interval and goodput.** For a 256-GPU W-TRAIN job, assume a blocking
checkpoint cost δ = 60 s, the canonical restart cost R = 900 s, and — as a deliberate pessimistic
*variation* on the canonical 48 h (= 1,536 node-h / 32 nodes) — a mean time between job-interrupting
failures M = 24 h `[ILLUSTRATIVE]` (node MTBF halved to 768 h).

1. Compute Young's interval τ and the three waste terms δ/τ, τ/(2M) and R/M.
2. Compute expected lost GPU-hours per failure.
3. If all other goodput losses (scheduling gaps, maintenance, stragglers) total 5 %, how long does
   the 2 × 10¹² token run take, given an ideal duration of 96.00 days?
4. Which single change would you put first in the backlog, and why?

*Evidence required:* arithmetic for each part; the backlog choice justified by numbers.

## C. Hands-on lab

**L1 ★★ L1 — Design-review linter.** Complete [lab/README.md](lab/README.md) Tasks 1–8: implement
`design_lint.py`, pass `python check.py`, produce `kestrel_lint.md`, write the triage memo, and lint
your own capstone bundle.
*Evidence required:* `check.py` output showing 13/13 PASS; the two reports; the triage memo.

## D. Troubleshooting case

**T1 ★★★ L1 (analysis) / L3 (re-run).** Kestrel's L3 extension ran `all_reduce_perf` (8 GiB, 4 nodes ×
8 GPUs) five times on a lab fabric that it shares with another team. Results `[ILLUSTRATIVE]` (node busbw over 8 rails): 329.6,
194.4, 318.4, 208.8, 324.0 GB/s. Their draft benchmark table reports "275.0 GB/s `[MEASURED]`" and
their design text concludes "the fabric loses 23 % at 4 nodes versus B-02's 356 GB/s; we lower A-06 to
34 GB/s per rail". Additional
evidence: the other team's job log shows it running during runs 2 and 4, and the switch's PFC pause
counters on rail-leaf ports for those two runs rose by ≈ 10⁶ frames versus < 10³ for runs 1, 3, 5.

1. What is wrong with the reported number and the conclusion?
2. Rank at least three hypotheses for the low runs and name a discriminating test for each.
3. Write the corrected benchmark-table row(s) and the assumptions-register change, if any.

*Evidence required:* median and mean computed; ranked hypotheses with tests; corrected rows with
labels.

## E. Design challenge

**D1 ★★★ L1.** Halcyon wants to grow ORION to 48 HX8 nodes (384 GPUs) for W-TRAIN, while the
inference team plans to run disaggregated serving with cross-rail KV-cache transfer on the same
backend next year. Rail-leaf ASICs are 51.2 Tb/s class, deployed either as 64 × 800G cages each run at 400G
(radix 64 at 400G) or broken out to 128 × 400G (radix 128). Compare at least three backend options:
(A) keep one radix-64 leaf per rail (64 × 800G cages at 400G) with 48 down / 16 up; (B) two such radix-64
leaves per rail at 1:1; (C) one 128 × 400G leaf per rail at 1:1. For each, compute leaf and spine counts and port usage,
oversubscription, backend cable count, and state which traffic crosses the spines. Recommend one
in an ADR with a revisit trigger. Include rack count and GPU-node power at 45 kW per rack.
*Evidence required:* the arithmetic per option; an ADR (context, options, decision, evidence,
consequences, revisit trigger).

## F. Reflection

**R1 ★ L1.** Which of your capstone's assumptions has the highest decision value, and what is the
cheapest test that would move it from `[ILLUSTRATIVE]` to `[MEASURED]`?

**R2 ★★ L1.** Name a class of design error that the lab's linter cannot catch, and describe how a
design review would catch it.

**R3 ★★ L1.** Young's model assumes independent failures. Describe one realistic correlated-failure
mechanism on ORION and its effect on the optimal checkpoint interval.

**R4 ★ L1.** What evidence would you still need before claiming your capstone design is
production-ready? List at least four items.

*Evidence required (R1–R4):* specific, ORION-grounded answers of 80–150 words each.

## G. Outline-mandated exercises (course outline Section 14, Chapter 23)

**M1 ★★★ L1 (L2/L3 optional) — Complete one capstone track.** Complete one of the capstone tracks
in [`capstones/`](../../../capstones/) (A–H) following its brief and
[`capstones/RUBRIC.md`](../../../capstones/RUBRIC.md).
*Evidence required:* every required artifact listed in the chosen brief; a design bundle that lints
with gate PASS (or with each remaining finding explicitly waived with a reason); evidence labels on
every number.

**M2 ★★★ L1 — Conduct a design review.** Run a design review of your capstone with at least two
reviewers who did not write it, covering explicit assumptions, trade-offs (ADRs), failure domains
and operational constraints. Use the Section 23.6 checklist (Table 23.7).
*Evidence required:* pre-read bundle, linter report, written findings with severities, the meeting
outcome, conditions with owners and dates, and the updated bundle.

**M3 ★★★ L1 (L2/L3 optional) — Present evidence, failure exercise and backlog.** Present your
benchmark evidence, failure-exercise results and a prioritised next-step backlog in a 20-minute
review talk (Table 23.9 structure).
*Evidence required:* slides with evidence labels visible per claim; failure-exercise report with
TTD/TTM/TTR and lost GPU-hours (labelled by tier); backlog with scoring and rationale.

## Chapter deliverable

**Complete capstone portfolio** (M1 + M2 + M3 together), structured so another engineer can review
and reproduce it. Chapter 24 shows how to turn it into a portfolio narrative.
