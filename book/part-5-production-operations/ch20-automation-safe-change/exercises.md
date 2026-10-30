# Chapter 20 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: **L1** laptop/simulation,
**L2** single host, **L3** multi-node lab fabric. Every exercise states the evidence required for
grading. Values are ORION `[ILLUSTRATIVE]` unless stated otherwise
([REFERENCE_CLUSTER.md](../../../docs/REFERENCE_CLUSTER.md)).

> **Safety:** All exercises target a simulation, a tabletop, or a dedicated lab environment. None
> asks you to change production or shared systems.

---

## 20.1 Knowledge check (★, L1)

Answer each in 2–5 sentences.

1. Define *idempotent* and give one ORION operation that is naturally idempotent and one that is
   not. For the second, explain how you would make it safe to retry.
2. What is the difference between a *level-triggered* and an *edge-triggered* controller? Why does
   the difference matter after the controller has been down for a day?
3. In Terraform/OpenTofu terms, what are *state*, *plan*, and *drift*? Which plan action should make
   a fabric reviewer stop and ask questions, and why?
4. Name the five validation layers of §20.5 and give one ORION defect that only layer 3
   (cross-object policy) can catch.
5. List the four OpenGitOps principles. What does GitOps do to a hand-applied break-glass fix, and
   how should a team handle break-glass under GitOps?
6. Distinguish *proceed*, *hold*, and *abort* in a rollout controller. Give a concrete condition
   that produces each.
7. Why should a rollout controller compare each node's median against *that node's own* baseline
   median, rather than against a fleet-wide threshold or a per-sample minimum?
8. Name five fleet-automation safety controls from Table 20.11 and the specific failure each
   prevents.

**Evidence required:** written answers; each answer names the mechanism, not just the term.

---

## 20.2 Worked problem A — MTU budget for an IPv6, VLAN-tagged variant (★★, L1)

A second cluster reuses ORION's design with three differences: the backend underlay is **IPv6**,
host ports are **802.1Q-tagged**, and the leaves' configured port MTU is **9,100 B**. The vendor
documents that the switch MTU counts the full frame including the Ethernet header, VLAN tag, and
FCS. Assume a 64-byte extended-header budget for IPv4, as in §20.5.1. The IPv6 header is 40 B
(IPv4 is 20 B).

a. What is the largest host IP MTU the leaves will forward without drops?
b. What is the minimum host IP MTU that carries a 4,096-byte RDMA payload, using a header budget
   adjusted for IPv6?
c. Is the ORION host MTU of 9,000 valid here? Show both inequalities.
d. Compute wire efficiency and packet rate at 400 Gb/s for RDMA MTU 1,024 and 4,096 on this
   variant. Per-packet wire overhead = preamble+SFD 8 + Ethernet 14 + 802.1Q 4 + IPv6 40 + UDP 8 +
   BTH 12 + ICRC 4 + FCS 4 + IFG 12.
e. Write the two policy rules (in pseudo-code or Python) with the thresholds read from policy data.

**Evidence required:** formula → substituted values → result with units for each part, and the
two rules.

---

## 20.3 Worked problem B — Wave plan for ORION-XL (★★★, L1)

ORION-XL has 512 HX8 nodes in 128 racks (4 nodes per rack). You are rolling out a NIC firmware
bundle. Constraints: at most one node per rack per wave; each wave costs 75 min (apply + verify +
60 min bake); nodes are drained for their wave.

a. A latent defect affects nodes with one board revision: 2 % of the fleet. With a random 8-node
   canary, what is the probability that the canary contains at least one affected node? How many
   randomly chosen nodes would you need for a 90 % probability?
b. The inventory identifies the 10 nodes with that revision. If you put 2 of them in the canary,
   and the defect manifests on an affected node during bake with probability 0.8, what is the
   detection probability?
c. Propose a wave plan (list of wave sizes) that respects the per-rack constraint and finishes in
   at most 8 waves. Compute total duration, peak fraction of GPUs out of service, and GPU-hours
   consumed.
d. After your first three waves, what is the probability that the 2 % defect has appeared at least
   once under *random* selection? What does that tell you about relying on wave size alone?

**Evidence required:** all arithmetic shown; a wave-size list that sums to 512 with the per-wave
maximum justified.

---

## 20.4 Hands-on lab — Safe-change automation (★★, L1; L2/L3 extensions)

Complete [Lab 20](lab/README.md), Parts 1–3. Then answer:

a. For each planted invalid desired value found by `validate_desired`, describe the RoCE failure it
   would have caused on ORION if applied.
b. Explain the two wave-1 situations that would make a naive controller abort, and the design
   choice in your controller that prevents each.
c. Justify `rollback_scope: all_changed` for this rollout, or argue for failing-wave-only.

**Evidence required:** `python check.py` output with all 13 checks PASS; the decision log from
`run_rollout`; written answers a–c (≤ 1 page). L2/L3: a filled-in copy of `lab/manifest.yaml` with
the extension fields.

---

## 20.5 Outline exercise — Idempotent node/network configuration validator (★★, L1 → L2)

Write an idempotent script, or an IaC/configuration-management example, that **validates** an
ORION node's backend network configuration against desired state and reports drift without
changing anything. Check, per backend NIC: IP MTU 9,000; RDMA active MTU 4,096; NIC firmware in
the approved list; link up at 400 Gb/s. Then add a `--apply` mode that fixes *only* the IP MTU, is
dry-run by default, and is a provable no-op on the second run.

Requirements:

- Read state through machine-readable interfaces where possible (`ip -j link show`,
  `ethtool -i <netdev>` for firmware, `ibv_devinfo` for `active_mtu`, link speed from
  `/sys/class/net/<netdev>/speed` or `ethtool <netdev>`).
- Exit code 0 = in sync, 1 = drift found, 2 = cannot determine (unreachable, missing tool).
- Emit one JSON audit line per check and per action (target, key, before, after, result).
- L1: run against a captured JSON fixture you create. L2: run on a lab VM (soft-RoCE acceptable).

**Evidence required:** source code; two consecutive runs showing drift → fixed → in sync (second
apply plans zero actions); the audit lines; for L2, the manifest fields from the lab README.

---

## 20.6 Outline exercise — Design a canary rollout for the leaf QoS profile (★★★, L1)

Design the rollout of a new RoCE QoS profile to ORION's 8 rail leaves (`orion-be-leaf-r0`–`orion-be-leaf-r7`). The
new profile tightens ECN marking thresholds on TC 3. Produce:

1. **Prechecks**: per-leaf and fabric-wide, with the exact signals.
2. **Wave plan**: which leaf first and why; wave sizes; bake time justified from Table 20.8.
3. **Success criteria**: measurable, per rail, with baseline method and thresholds.
4. **Abort conditions**: at least four, each with statistic, threshold, and floor where relevant.
5. **Rollback**: mechanism, scope, rehearsal evidence, time bound.
6. **Audit evidence**: what is recorded per leaf and per wave, and where.

**Evidence required:** a 1–2 page design using the six headings; every threshold labelled
`[ILLUSTRATIVE]` or derived from a stated baseline; explicit reasoning about rail independence.

---

## 20.7 Outline exercise — Review a deliberately unsafe change plan (★★, L1)

Review `lab/data/unsafe_change_plan.md` (this is Lab Part 3). Identify missing validation,
blast-radius controls, and rollback mechanisms, recording them as structured findings in
`findings.yaml`. Then rewrite the plan as a safe change, or rather as **three** changes.

**Evidence required:** `findings.yaml` passing the three Part 3 checks; a rewritten plan (≤ 2
pages) that addresses every finding, with wave plan, abort conditions, and rollback.

---

## 20.8 Troubleshooting case — The plan that wanted to remove PFC (★★★, L1)

At 02:10 the nightly fabric reconciler posts this dry-run plan for review (it normally plans 0–3
actions):

```text
[ILLUSTRATIVE] reconciler dry-run  change=nightly-reconcile  desired=commit 41aa9d3 (unchanged since yesterday)
plan: 16 targets, 48 actions
  orion-n17  pfc_priorities   [3]   -> []
  orion-n17  ecn_enabled      true  -> false
  orion-n17  trust_mode       dscp  -> pcp
  ... (same three actions for orion-n18 .. orion-n32)
```

Supporting evidence:

```text
[ILLUSTRATIVE] reconciler log
02:09:58 inventory GET /api/groups/roce-lossless/members  status=200  items=16  next=/api/groups/roce-lossless/members?page=2
02:09:58 render: 16 targets in group roce-lossless -> profile lossless-v3
02:09:58 render: 16 targets not in any lossless group -> profile default (lossy)
02:10:01 diff complete: 48 actions
```

Nobody changed the desired-state repository. Yesterday's run planned 0 actions.

a. Rank three hypotheses and name the discriminating evidence for each.
b. Identify the root cause.
c. What would have happened with no safety controls? Which controls in Table 20.11 stop it?
d. Specify the fix and the validation, plus one new guard that prevents this class of defect.

**Evidence required:** ranked hypotheses with discriminating tests; root cause tied to specific log
lines; fix, validation, and guard.

---

## 20.9 Design challenge — Drift policy and break-glass for the ORION fabric (★★★, L1)

Platform and Fabric disagree. Fabric wants the GitOps controller to **auto-revert** any drift on
leaf QoS and MTU within 5 minutes. Platform wants **alert-only**, because on-call engineers
sometimes need to hand-tune ECN thresholds during incidents. Propose a policy covering which fields
auto-revert, which alert, how break-glass works (who, how long, how recorded, how it expires), and
how you prevent the fighting-writers failure of §20.13. Defend it with at least two failure
scenarios.

**Evidence required:** a policy table (field class × behaviour × rationale), a break-glass
procedure, and two scenario walk-throughs showing the policy's behaviour.

---

## 20.10 Chapter deliverable — Automation sample and safe-change runbook (★★★, L1)

Submit:

1. **Automation sample**: your completed Lab 20 Parts 1–2 (the reconciler and rollout controller)
   or your Exercise 20.5 validator, with a README explaining its safety defaults: dry run, cap,
   audit, and kill-switch hook.
2. **Safe-change runbook** for one ORION change type of your choice (NIC firmware, leaf QoS, or host
   MTU), following the structure of the runbook excerpt in the manuscript: before / during / after,
   signals and thresholds table, abort and rollback procedure, escalation, and audit bundle
   contents.

**Evidence required:** both artefacts; the runbook cites the lab's decision log or your Exercise
20.6 design as its threshold source.

---

## 20.11 Reflection / review (★, L1)

1. The §20.11 expected-loss comparison found a big-bang change *cheaper* in expected GPU-hours.
   Under what conditions would you accept the big bang, and what evidence would you need?
2. The Part 2 controller saw synthetic metrics. List three things real telemetry would do that the
   lab data does not, and how each could fool your controller.
3. Your Part 3 score is keyword-based. Identify one of your findings that would pass the checker
   but that a senior reviewer might still reject, and improve it.
4. What evidence is still missing before you could claim that raising RDMA MTU to 4,096 improves
   ORION's training step time?

**Evidence required:** written answers, ≤ 150 words each, naming specific missing evidence.
