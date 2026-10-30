# Chapter 19 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/paper · L2 one GPU
host · L3 multi-node RDMA lab partition. Reliability numbers use the Reference Cluster canon: node MTBF
≈ 1,536 node-hours, restart overhead ≈ 15 min `[ILLUSTRATIVE]`. Answers: `solutions/exercises-key.md`.

**Chapter deliverable (course outline):** **risk register** (M1), **isolation model** (M2), and
**recovery test plan** (M3); plus the Section 20.1 evidence pack from the 512-node incident (M4 / Lab 19):
failure timeline, rank-to-hardware mapping, health decision, checkpoint/restore validation, recovery
metrics, and postmortem.

---

## Knowledge checks

**K1 ★ L1 — Scale and MTBF.** Compute job MTBF and expected interruptions per day for jobs of 8, 32,
128, and 512 HX8 nodes.
*Evidence required:* formula and a four-row table.

**K2 ★ L1 — Row-remapper states.** For each state, give the action and why: (a) Pending = Yes;
(b) Remapping Failure Occurred = Yes; (c) Correctable = 1, Pending = No, Failure = No.
*Evidence required:* three actions with a one-line mechanism each.

**K3 ★★ L1 — Reading Xids.** A node logs Xid 13 in one job, Xid 79 the next day, and Xid 94 the week
after. For each: hardware or application? What do you do with the node?
*Evidence required:* classification and action per code, citing Table 19.3, with the vendor-document
caveat.

**K4 ★ L1 — PCIe evidence.** Distinguish correctable, uncorrectable non-fatal, and fatal AER errors.
What does `LnkSta: Speed 32GT/s, Width x8` under `LnkCap: … Width x16` mean for a GPU's achievable
host bandwidth?
*Evidence required:* three definitions; bandwidth before/after in GB/s per direction.

**K5 ★ L1 — The first reporter.** Why is the first rank to log a watchdog timeout usually not the
culprit? Name the two artefacts that localise a hang.
*Evidence required:* mechanism of the watchdog; two artefacts.

**K6 ★★ L1 — Domain vs unit.** Explain the difference between the *fault domain* and the *scheduling
unit removed* for a failed `mlx5_3` link on a node running a TP = 8, rail-optimized job. When could the
two coincide?
*Evidence required:* both definitions applied; one coinciding case.

**K7 ★ L1 — Sharing a GPU across tenants.** Compare whole-GPU, MIG, and time-slicing for two tenants on
one H100-class GPU: memory isolation, fault isolation, performance isolation.
*Evidence required:* a 3 × 3 table.

**K8 ★★ L1 — Reachability vs performance.** Tenants A and B have different VRFs and VNIs on ORION's
shared RoCE fabric. Explain how B's job can still slow A's, and two mitigations.
*Evidence required:* mechanism through shared links/PFC; two mitigations.

## Worked problems

**W1 ★★ L1 — Checkpoint interval and restart overhead.**
(a) For a 32-node ORION job (δ = 1 min blocking checkpoint cost, R = 15 min), compute τ_opt and goodput.
(b) For a 512-node ORION-XL job at τ = 19 min, compute goodput with R = 15 min and with R = 5 min.
(c) Convert the difference in (b) into GPU-hours per day and dollars per day at $3/GPU-h.
*Evidence required:* Young's formulas with substitutions; results to 3 significant figures.

**W2 ★★★ L1 — Retry budgets and spares.**
(a) After an upgrade to NCCL 2.23 or later the `NCCL_IB_TIMEOUT` default becomes 20 (it was 18 up to
2.22). With `NCCL_IB_TIMEOUT=20` and `NCCL_IB_RETRY_CNT=7`, compute the retry budget. Which of the lab's
flaps (14 s, 6 s, 5 s, 14 s) would now be survived?
(b) What do you lose by raising the timeout? Quantify for a 4,096-GPU job whose peer has *died*.
(c) Size a declared ORION-XL spare pool (a variation; the reference cluster has none) with the Chapter 16
Poisson method at P(in repair ≤ k) ≥ 0.99, for repair turnaround of 3 days and of the canonical 5 days.
Express each as a percentage of the 512-node partition.
*Evidence required:* arithmetic for each part; a recommendation with its trade-off.

## Hands-on lab

**L1 ★★★ L1 — Lab 19: ORION-XL incident** ([lab/README.md](lab/README.md)). Implement
`lab/starter/incident_toolkit.py`, pass `python check.py`, and submit the incident packet.
*Evidence required:* 12/12 PASS; `incident_packet.md` per lab README Section 8.

## Troubleshooting case

**T1 ★★ L1 — The quiet downtrain.** A 16-node job on ORION runs 9 % slower than its baseline since a
maintenance reboot of orion-n10 yesterday. Evidence `[ILLUSTRATIVE]`:

```text
per-node SM active: 15 nodes 0.57, orion-n10 0.57    (no compute straggler)
per-node backend NIC TX (Gb/s, 8 NICs summed): 15 nodes 1,050-1,080, orion-n10 985
orion-n10 rdma statistic: out_of_sequence flat; rp_cnp_handled normal; link_downed 0
orion-n10 journalctl -k | grep AER: 3,400 "Corrected error ... type=Physical Layer ... RxErr" since boot (others: 0-5)
orion-n10 lspci -vvv -s 3b:00.0 (mlx5_2):  LnkCap: Speed 32GT/s, Width x16   LnkSta: Speed 32GT/s, Width x8 (downgraded)
switch counters for all 8 orion-n10 ports: clean
```

Run the diagnostic loop: hypotheses, discriminating evidence, root cause, containment (domain and
unit), fix, validation. Explain why SM activity does not single out orion-n10 here, unlike the Chapter 18
power-cap case.
*Evidence required:* hypothesis table; bandwidth arithmetic for x16 vs x8; containment decision;
validation criteria.

## Design challenge

**D1 ★★★ L1 — Hot spares vs elastic training.** A 512-node ORION-XL job runs TP = 8, PP = 8, DP = 64, so one
DP replica is 8 nodes. Halcyon can either (A) keep a declared, Poisson-sized (P99) spare pool outside the
partition and restart at fixed world size (R = 15 min), or (B) use elastic training with no spares that
drops whole DP replicas and re-shards in 5 minutes. Using the canonical MTBF and 5-day MTTR, compare
expected useful throughput per *fleet* node for A, for B with rank re-packing, and for B without it
(expected and worst case). Address global-batch divisibility when DP changes, and recommend.
*Evidence required:* model with assumptions; numeric comparison; recommendation with risks.

## Reflection / review

**R1 ★ L1** — Which statements in your lab packet rely on *intervention* evidence that does not yet
exist? How will you obtain it?

**R2 ★★ L1** — The lab assumes synchronised clocks. Which conclusions would change with a 15 s skew on
orionxl-n212?

**R3 ★★ L1** — Give two ways an over-aggressive auto-quarantine policy reduces reliability.

**R4 ★ L1** — Which isolation violation in the lab is the most severe, and why?

*Evidence required (R1–R4):* concise answers that cite data files or sections.

## Outline-mandated exercises

**M1 ★★ L1 — Failure-mode analysis.** Perform an FMEA for **GPU node, rack, leaf switch, storage,
scheduler, and control-plane** failures on ORION-XL: failure modes, effects on training and inference,
S/O/D with justification, RPN and action priority, detection controls, mitigations, owners.
*(Deliverable: risk register.)* The lab's `fmea_score()` may be used to rank it.
*Evidence required:* ≥ 12 rows covering all six domains; corrected scores; top-5 actions with owners.

**M2 ★★ L1 — Tenant isolation boundaries.** Define isolation boundaries for **identity, network,
storage, GPU allocation, secrets, and audit logs** for three ORION-XL tenants (two training, one
inference). *(Deliverable: isolation model.)* Express the policy machine-readably and check it with the
lab's `check_isolation()`.
*Evidence required:* boundary table; policy YAML; checker run showing zero violations on your config.

**M3 ★★★ L1 — Recovery and containment exercise.** Design a recovery exercise that **tests fault
containment and validates that one tenant's failure does not disrupt another**: hypothesis, steady-state
SLIs, injection (dedicated lab partition only), abort criteria, observations, pass criteria, evidence.
*(Deliverable: recovery test plan.)*
*Evidence required:* complete plan per Section 19.10; at least three injections; explicit safety
controls; **and a tabletop run report** — walk the plan with the owning teams, record for each injection
the expected vs "discovered" behaviour, the gaps found, and the follow-up actions.

**M4 ★★★ L1 — 512-node incident (Section 20.1).** Given the synthetic 512-node training incident with
one flaky HCA, one GPU ECC fault, and an NCCL timeout (Lab 19), correlate logs and telemetry, identify
the smallest failure domain, quarantine the suspect component, and produce a safe restart plan.
Distinguish proven cause from correlation. Submit the failure timeline, rank-to-hardware mapping, health
decision, checkpoint/restore validation, recovery metrics, and a postmortem (Chapter 18 template).
*Evidence required:* checker PASS; the six artefacts.
