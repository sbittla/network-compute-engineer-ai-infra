# Chapter 16 — Exercises: Bare-Metal GPU Fleet Lifecycle

Tags: difficulty ★ foundational, ★★ intermediate, ★★★ advanced; tier L1 (laptop), L2 (one GPU host),
L3 (multi-node GPU + RDMA). Every exercise states the **evidence required** for grading. All values
are from the ORION reference cluster unless an exercise varies them explicitly. Exercises marked
**[Outline]** are mandated by the course outline; **D1** is the chapter deliverable.

---

## A. Knowledge checks

**K1 ★ (L1).** List the eight lifecycle states of Figure 16.1 in order and name the *only* two states
from which a node may enter `schedulable`. Why is there no edge `repair → schedulable`?
*Evidence required:* the eight states; the two source states; one sentence of justification.

**K2 ★ (L1).** On an idle HX8, `nvidia-smi` reports `pcie.link.gen.current = 1` and
`pcie.link.width.current = 16` for GPU 0. Under a burn-in load it reports Gen 5 x16. Is this a
defect? What would make it one?
*Evidence required:* verdict with the mechanism (idle power management) and the condition that
would indicate a defect.

**K3 ★ (L1).** Explain the difference between a *pending* row remap and a *remapping failure* on an
H100-class GPU, and give the correct operational action for each.
*Evidence required:* definitions; one action each; which one is an RMA candidate.

**K4 ★ (L1).** A burn-in log shows `SW Power Cap: Active` on all 8 GPUs and `SW Thermal Slowdown:
Active` on GPU 6. Which reason(s) fail acceptance and why?
*Evidence required:* the failing reason; why the other is normal; two plausible physical causes.

**K5 ★★ (L1).** Why does a validated-bundle compatibility matrix beat a pairwise "A works with B"
table? Give one concrete three-way interaction from Table 16.5 that a pairwise table can miss.
*Evidence required:* the combinatorial argument; one named three-component interaction.

**K6 ★ (L1).** Name the Redfish resource you would use to (a) set a one-time PXE boot, (b) reset the
system, and (c) list the firmware actually installed. Why must automation read back the running
version after a firmware update?
*Evidence required:* three resource paths or actions from Section 16.3; the staged-vs-running
explanation.

**K7 ★★ (L1).** In NIST SP 800-88 terms, what category does an NVMe Sanitize crypto erase fall into,
and why is it preferred over overwriting the file system before retiring a node?
*Evidence required:* the category (Purge); the over-provisioning / remapped-block argument; what
gets recorded.

---

## B. Worked problems

**W1 ★★ (L1) — Staged upgrade for ORION-XL.** ORION-XL has 512 HX8 nodes in 128 racks of 4. You must
move it to a new bundle. Policy: canary of 4 nodes in 4 different racks with a 72 h bake; waves of at
most 32 nodes and at most 1 node per rack; each wave takes 3 h; 6 h bake between waves.
(a) How many waves after the canary? (b) Calendar time for the campaign? (c) Node-hours and
GPU-hours out of service? (d) Probability the canary catches a regression with an intermittent fault
rate of λ = 1 per 100 node-hours, and of λ = 1 per 1,000 node-hours. (e) How many canary node-hours
would give 90 % detection at λ = 1 per 1,000 node-hours, and what does that imply about canaries for
rare faults?
*Evidence required:* every formula, substituted values, and result with units; a two-sentence
conclusion for (e).

**W2 ★★ (L1) — What a degraded node costs.** W-TRAIN on ORION (step 17.4 s at 40 % MFU, TP 8, PP 4,
DP 8). (a) One GPU runs at 85 % throughput; assume 70 % of the step is compute on the critical path
and 30 % exposed communication. Compute the new step time, throughput loss, and GPU-equivalents lost.
(b) One compute NIC's PCIe link trains at Gen5 x8 instead of x16. Compute the PCIe ceiling per
direction, assume 85 % of it is achieved, and compute the extra DP all-reduce time per step for the
7.66 GB per GPU of Section 16.6, as a percentage of step time. (c) Which defect is worse for this job,
and why must acceptance reject both anyway?
*Evidence required:* arithmetic for each part; the critical-path argument in (c).

---

## C. Hands-on lab

**L1 ★★ (L1) — Fleet lifecycle automation.** Complete [lab/README.md](lab/README.md) Tasks 1–5:
`check_compat`, `evaluate_node`, the lifecycle state machine with audit log, the upgrade-wave
planner, and the acceptance report.
*Evidence required:* `python lab/check.py` output showing 33/33 PASS; your `acceptance_report.md`
listing every non-PASS node with codes, the raw evidence values that triggered them, and the
remediation; the list of rejected lifecycle events with reason codes.

---

## D. Troubleshooting case

**T1 ★★★ (L1 tabletop; L2/L3 to reproduce signals) — The afternoon slowdown.** Training Infra reports
that a 128-GPU job has a step-time p99 that is 9 % above p50 every afternoon, and only when it is
placed on nodes in rack-04. The nodes passed acceptance three months ago. Evidence:

```text
# nvidia-smi --query-gpu=index,temperature.gpu,clocks.sm,clocks_event_reasons.active --format=csv (orion-n14, 15:10)
4, 86, 1650 MHz, 0x0000000000000024
5, 87, 1590 MHz, 0x0000000000000024
6, 79, 1980 MHz, 0x0000000000000004
# same query at 03:10: all GPUs 71–76 C, 1980 MHz, 0x0000000000000004
# BMC inlet temperature (ipmitool sdr type Temperature), rack-04 nodes:
            03:00   09:00   15:00
orion-n13   23 C    25 C    31 C
orion-n14   23 C    26 C    32 C
orion-n15   24 C    25 C    31 C
orion-n16   23 C    25 C    32 C
# rack-03 and rack-05 nodes at 15:00: 24–25 C inlet
# Facilities ticket FAC-2210 (2 weeks ago): "rack-04 cold-aisle containment door panel removed for cable work"
```

Clock-reason bitmask reference (verify for your driver): `0x4` = SW Power Cap, `0x20` = SW Thermal
Slowdown. (1) Decode the reasons. (2) Rank three hypotheses. (3) Name the discriminating test for
each. (4) State root cause, the safe change, and how you validate it. (5) Which lifecycle actions, if
any, are appropriate for the four nodes?
*Evidence required:* decoded bitmask; ranked hypotheses with discriminating tests; a root cause that
explains *time of day* and *rack locality*; a validation measurement with a pass threshold; a
lifecycle decision with justification.

---

## E. Design challenge

**DC1 ★★★ (L1) — Tiered return-to-service.** Full acceptance takes ≈ 25 h. Repair data show that 60 %
of repairs are optic/cable swaps, 25 % NIC swaps, 10 % GPU or baseboard swaps, and 5 % DIMM/NVMe
swaps [ILLUSTRATIVE]. Design a *tiered* re-acceptance policy that picks the acceptance depth from
what was replaced, without weakening the "only through `validated`" rule. Estimate the average
re-acceptance time under your policy versus full acceptance, and identify the failure mode your
policy could miss and how you would detect it in production.
*Evidence required:* a table mapping repair type → tests; a weighted-average time calculation; one
named residual risk with a detection signal and threshold.

---

## F. Outline-mandated exercises

**M1 ★★ (L1; L2/L3 to execute) [Outline] — Node acceptance test design.** Design a node acceptance
test for an HX8 covering accelerator discovery, memory checks, NIC link validation, storage, thermals,
and burn-in (and, beyond the outline minimum, NVLink/fabric state, RDMA pair bandwidth, and a
single-node NCCL test). For each check give: the command or tool, what is measured, pass criterion,
FAIL vs WARN classification, approximate duration, and the order in which checks run.
*Evidence required:* a table with ≥ 12 checks in fail-fast order; every threshold labelled with its
evidence class; a total duration estimate; the policy-version field you will record.

**M2 ★★★ (L1) [Outline] — Compatibility matrix and staged upgrade plan.** Using
`lab/data/compat_matrix.yaml` as a starting point, (a) extend the matrix with the components it
omits (fabric manager, CUDA user-mode, DCGM, NVIDIA container toolkit, NVMe firmware, PSU firmware)
and state the coupling rule for each; (b) write the staged upgrade plan from B-2026.04 to B-2026.10
for the 32 ORION nodes: qualification, canary (size, placement, bake time with a detection-probability
calculation), wave sizes and per-rack caps, maintenance windows aligned with W-TRAIN checkpoints,
pre-declared abort conditions with thresholds, a per-component rollback table (including at least
one non-reversible component), and the audit evidence you will keep.
*Evidence required:* the extended matrix; the plan with every number derived; the rollback table;
the abort-condition list; the evidence list.

**M3 ★★ (L1) [Outline] — Lifecycle state machine.** Write the node lifecycle state machine with
states discovered, imaged, validated, schedulable, draining, drained, repair, and retired: every
allowed transition with its event, guard, side effects, and audit fields; and the transitions you
deliberately forbid, with the reason. Implement it (lab Task 3) and show the rejected events from the
replay.
*Evidence required:* a diagram; a transition table; a forbidden-transition table; `check.py` T3.*
checks passing.

---

## G. Reflection and review

**R1 ★ (L1).** The lab's acceptance thresholds are teaching values. Describe how you would derive
real thresholds from a population of known-good nodes, including how many runs per node and which
statistic you would use.
*Evidence required:* a procedure naming repetitions, statistic (e.g., median and spread), and margin.

**R2 ★★ (L1).** The worked example assumed independent failures. Name two real mechanisms that make
failures correlated across nodes and explain how each changes your canary and wave design.
*Evidence required:* two mechanisms; one design change each.

**R3 ★ (L1).** What evidence would you still be missing if acceptance passed but a node later caused
a multi-node NCCL hang? Which chapter's tests cover that gap?
*Evidence required:* at least two missing evidence types; chapter cross-references.

**R4 ★★ (L1).** Your lab evaluator returns `FW_OFF_MATRIX` for a node whose only difference is one
NIC on a newer, not-yet-qualified firmware that the vendor says fixes a bug you have hit. Argue
whether to waive, reflash, or fast-track a bundle, and what evidence each choice requires.
*Evidence required:* a decision; the evidence and approval path for it.

---

## H. Chapter deliverable

**D1 ★★★ (L1; L2/L3 optional) — Node acceptance automation specification and lifecycle runbook.**
Produce a document of 4–8 pages containing: (1) the acceptance specification (from M1) as a policy
file plus rationale; (2) the evaluator's input schema and reason-code catalogue (from the lab);
(3) the lifecycle state machine (from M3) with the audit-record schema; (4) the compatibility-matrix
process and the staged-upgrade procedure (from M2); (5) a runbook for "node fails acceptance" and
"node develops a hardware fault in production", with signals, thresholds, safe actions, evidence to
capture, and escalation paths; and (6) a realism section stating which parts were validated at L1
only.
*Evidence required:* the document; your lab `acceptance_report.md` as an appendix; `check.py` output;
for L2/L3, the filled `manifest.yaml` and raw command outputs.
