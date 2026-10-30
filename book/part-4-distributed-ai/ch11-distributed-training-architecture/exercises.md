# Chapter 11 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/simulation, L2 single GPU
host, L3 multi-node GPU + RDMA. Unless stated, use W-TRAIN on ORION-256 and the assumptions in
Table 11.4 of the manuscript. Label every number you produce `[MODELED]`, `[MEASURED]`, or
`[ILLUSTRATIVE]`.

**Chapter deliverable (course outline):** *parallelism design, timing model, and recovery plan* —
assembled from Exercises 11.10 (O1), 11.11 (O2), 11.12 (O3), and the lab report.

---

## Knowledge checks

**11.1 ★ L1 — Collectives per strategy.** For each of DDP, ZeRO-1, ZeRO-3/FSDP, Megatron TP with
sequence parallelism, pipeline parallelism, and expert parallelism, name the collective(s) used and how
often they run per optimizer step (per step, per micro-batch, per layer per micro-batch).
*Evidence required:* a six-row table with collective names and frequencies.

**11.2 ★ L1 — Bytes per parameter.** Explain where each of the 16 bytes per parameter of BF16
mixed-precision Adam goes, and give the bytes per local parameter for ZeRO-1, ZeRO-2, and ZeRO-3 with
DP = 8. *Evidence required:* a breakdown and three numbers.

**11.3 ★ L1 — Bubble.** Compute the 1F1B bubble fraction (of total time) for p = 4 with m = 8, 32, and
128, and for p = 8 with m = 32. *Evidence required:* four values with the formula shown.

**11.4 ★ L1 — Why sequence parallelism?** Sequence parallelism does not reduce TP bytes on the wire.
What does it reduce, and by how much for TP = 8? *Evidence required:* two sentences naming the
quantity and the factor.

**11.5 ★★ L1 — Rail locality.** With Megatron's TP-fastest rank order, TP = 8, and `torchrun
--nproc-per-node=8`, prove that every DP peer of global rank 19 is attached to rail leaf 3.
*Evidence required:* the rank arithmetic.

**11.6 ★★ L1 — The timeout victim.** Explain why the first rank to log an NCCL watchdog timeout is
usually not the faulty rank, and name two artifacts that identify the faulty one.
*Evidence required:* explanation plus two named artifacts.

**11.7 ★ L1 — MFU versus recompute.** A team turns on full activation recomputation and reports that
"hardware FLOP/s went up 8 %". Did MFU go up? *Evidence required:* one-paragraph answer referencing
the MFU definition.

## Worked problems

**11.8 ★★ L1 — Memory audit.** For TP = 4, PP = 4, DP = 16, micro-batch 2, ZeRO-1, selective
recompute, compute per-GPU model state, activations on stage 0, total, and say whether it fits the
68 GB planning limit. *Evidence required:* every intermediate value with units.

**11.9 ★★ L1 — Communication budget.** For the baseline, compute per-GPU bytes per step for TP, DP,
and PP, convert each to time with Table 11.4, and say which one you would attack first and why.
Then repeat the TP number for TP = 2 and explain the (t − 1) identity.
*Evidence required:* three volumes, three times, the TP = 2 result, and a one-sentence priority.

## Outline-mandated exercises

**11.10 (O1) ★★ L1 — Choose a parallelism for three constraints.** For each workload, choose data,
tensor, pipeline (or a combination, with ZeRO if needed) on ORION and explain the communication
implications (collective, volume per step, link used):

- (a) a 1.3B-parameter model, sequence 2,048, global batch 512, 64 GPUs;
- (b) W-TRAIN at sequence 4,096 but restricted to 64 GPUs (8 nodes) with global batch 256;
- (c) a 70B model fine-tuned at sequence 65,536 on 32 GPUs, global batch 32.

*Evidence required:* for each case, the chosen (TP, PP, DP, CP, ZeRO stage), a memory estimate showing
it fits, the dominant traffic with bytes per GPU per step, and which ORION links carry it.

**11.11 (O2) ★★ L1 — Step-time sensitivity.** Starting from the baseline breakdown
(compute 13.92 s, bubble 0.33 s, exposed TP 3.08 s, exposed DP 0.098 s, exposed PP 0.028 s), estimate
the new step time and MFU when: (a) kernel efficiency rises from 0.50 to 0.55; (b) TP overlap rises
from 25 % to 60 %; (c) one rank of 256 runs its compute 8 % slower (straggler; synchronization
overhead); (d) DP time triples because of fabric congestion; (e) both (b) and (c). Rank the levers.
*Evidence required:* five step times and MFUs with arithmetic, and the ranking with one sentence each.

**11.12 (O3) ★★★ L1 — Failure-aware training workflow.** Design the checkpoint-and-restart workflow
for W-TRAIN on (a) ORION-256 and (b) ORION-XL (4,096 GPUs), using the canonical job MTBF of 48 h and 3 h
(1,536 node-hours / nodes), C = 45 s (synchronous) or 5 s (asynchronous), and R = 900 s. Give τ_opt, expected waste, expected lost work
per failure in GPU-hours, and lost GPU-hours per day. Then state the restart procedure (detection,
isolation, replacement, restore, validation) and the retry/quarantine policy, and say which term
(C, R, or MTBF) you would invest in at each scale.
*Evidence required:* a table of the eight numbers per scenario, a state diagram or numbered
procedure, and an investment recommendation justified by the numbers.

## Hands-on lab

**11.13 ★★ L1 — Step-time and memory model (lab).** Complete [lab/README.md](lab/README.md) tasks
1–6 so that `python lab/check.py` passes, and write the lab report.
*Evidence required:* checker output (10/10 PASS), candidate table, recommendation with justification,
checkpoint table, and a paragraph on the planted traps.

## Troubleshooting case

**11.14 ★★★ L1 — The quiet 8 %.** After a firmware maintenance window, W-TRAIN's step time is
18.8 s p50 (baseline 17.45 s). Per-rank logs show: ranks 0–255 compute 13.9–14.0 s except ranks 96–103
at 15.2 s; DP comm unchanged; TP comm unchanged on all nodes; every rank except 96–103 shows
≈ 1.3 s more "pp_wait" or collective wait than baseline. `nvidia-smi -q -d PERFORMANCE` on `orion-n13`, the node
hosting ranks 96–103, shows `SW Power Cap: Active`. Walk the diagnostic loop: rank hypotheses, name
discriminating tests, identify the root cause, propose a safe fix and the validation evidence.
*Evidence required:* ranked hypotheses (≥ 3), tests with expected outcomes, root cause, fix,
validation criteria, and an estimate of GPU-hours lost per day.

## Design challenge

**11.15 ★★★ L1 — 8k sequences next quarter.** Research wants W-TRAIN at sequence 8,192 with the same
global batch in tokens (512 sequences). Propose a layout for ORION-256, show it fits under 68 GB, and
estimate the step time with the lab model (edit `model_wtrain.yaml`). Defend your choice against one
alternative on memory, communication, and risk.
*Evidence required:* the config, memory and step-time output from the tool, and a trade-off table.

## Reflection

**11.16 ★ L1.** Which three assumptions in Table 11.4 would you measure first on real hardware, and how?

**11.17 ★ L1.** The model says DP communication is < 1 % of step time. Name two real effects that could
make DP matter much more than the model suggests.

**11.18 ★★ L1.** Why is "the configuration fits in 80 GB" an insufficient acceptance criterion?
What evidence would you require?

**11.19 ★★ L1.** The Young/Daly formula assumes exponentially distributed failures. Describe one real
failure pattern that violates this and how it changes your checkpoint policy.

## Optional: fault-isolation tabletop (outline §20.1, developed in Chapter 19)

**11.20 ★★★ L1 — From timeout to restart.** A 512-node W-TRAIN-class job logs an NCCL watchdog timeout
at 03:12. In the preceding 20 minutes: node `orionxl-n312` logged a GPU uncorrectable ECC event (Xid 48-class)
on GPU 5 at 02:58; NIC 2 of `orionxl-n141` logged 14 link-down/up events since 01:00; and the job's step
time on ranks of `orionxl-n141` rose 6 % at 01:05. Using the rank-to-hardware mapping rule of Section 11.8
(TP fastest, 8 ranks per node; the job's node list is `orionxl-n[001-512]` in rank order, so node
`orionxl-nNNN` hosts global ranks 8(NNN − 1) … 8(NNN − 1) + 7), identify the global ranks involved, decide which component most
likely caused the timeout and which is a correlated-but-separate problem, choose the smallest failure
domain to quarantine for each, and write the restart plan (checkpoint choice, replacement nodes,
validation). Distinguish proven cause from correlation.
*Evidence required:* timeline, rank-to-hardware table, health decision per component, restart plan,
and one sentence on what evidence would *prove* the cause.
