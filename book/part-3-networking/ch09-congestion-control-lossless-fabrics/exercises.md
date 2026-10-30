# Chapter 9 — Exercises

Difficulty: ★ foundational, ★★ intermediate, ★★★ advanced. Tier: L1 laptop/paper, L2 single host,
L3 multi-node RDMA lab fabric. Unless stated, use ORION values from
[REFERENCE_CLUSTER.md](../../../docs/REFERENCE_CLUSTER.md) and the chapter's assumptions
(v ≈ 2 × 10⁸ m/s in fibre, i.e. 5 ns/m; port MTU 9,216 B; t_resp = 1 µs). Label every number you
produce `[MODELED]`, `[SIMULATED]`, `[MEASURED]`, or `[ILLUSTRATIVE]`.

**Chapter deliverable (course outline):** *congestion diagnosis, experiment plan, and mitigation
proposal* — produced by Exercise H1 (with O1–O3 feeding into it).

---

## Knowledge check

**K1 ★ L1 — Roles.** In the 12:1 incast of Section 9.7, name the device that plays each DCQCN role
(CP, NP, RP) and the packet that travels from NP to RP, including its ORION DSCP and traffic class.
*Evidence required:* three device names, the packet name, DSCP and TC values.

**K2 ★ L1 — Pause arithmetic.** Compute the duration of one PFC pause quantum and of the maximum
single-frame pause (65,535 quanta) at 100 Gb/s and at 400 Gb/s. Why does a sustained pause appear as a
*rate* of pause frames in counters?
*Evidence required:* four values with formula and units; one-sentence explanation.

**K3 ★ L1 — ECN codepoints.** Give the IP ECN bit patterns for Not-ECT, ECT(0), ECT(1), and CE. Above
Kmin, what does a switch with both WRED and ECN enabled on a queue do to an ECT packet, and to a
Not-ECT packet? Why must the second behaviour never occur in ORION's TC 3?
*Evidence required:* four bit patterns; two behaviours; one reason.

**K4 ★★ L1 — CNP class.** ORION carries CNPs in DSCP 48 / TC 6 with strict priority. Explain what goes
wrong, step by step, if a leaf maps CNPs into TC 3 instead.
*Evidence required:* a causal chain of at least three steps ending in an observable counter symptom.

**K5 ★★ L1 — Xoff and headroom.** Explain the difference between the Xoff threshold and the headroom
reservation. What is the observable symptom of undersized headroom, and why does it usually appear on
the longest links first?
*Evidence required:* two definitions; symptom naming a specific counter; reason tied to the formula.

**K6 ★★ L1 — Direction of pause.** Switch port P reports a high `pfc_tx_p3` rate. Port Q reports a high
`pfc_rx_p3` rate. For each, state whose buffer is filling and who is being asked to stop.
*Evidence required:* two correct statements.

**K7 ★ L1 — Watermarks.** A dashboard samples instantaneous queue depth every 10 s and shows ≤ 20 KB at
all times, yet ECN-marked counters increase by 2 million per interval. Explain the contradiction and
what you would plot instead.
*Evidence required:* explanation and the replacement metric.

**K8 ★ L1 — Storm or incast.** Using Table 9.4, list four signals that distinguish a PFC storm source
from an incast destination on the switch port facing the device.
*Evidence required:* four signals with the expected value for each case.

---

## Worked problems

**W1 ★★ L1 — Headroom budget.** A 64-port, 400 Gb/s spine has all ports on 150 m fibre runs. Two
priorities are lossless.
(a) Compute the headroom per port per lossless priority.
(b) Compute the total headroom reservation for the switch.
(c) Repeat (a) for 800 Gb/s with the same cable, MTU, and response time, and comment on how headroom
scales with link speed.
*Evidence required:* every term of the formula substituted with units; three results; one-sentence
comment.

**W2 ★★ L1 — Incast and feedback.** Sixteen senders each send 2 MB simultaneously to one 400 Gb/s
destination port. The port's Xoff-equivalent threshold is 1.5 MB, its buffer share 6 MB, base RTT 6 µs,
DCQCN CNP interval N = 50 µs, initial α = 1.
(a) Excess arrival rate in KB/µs. (b) Time to reach the threshold. (c) Can ECN feedback arrive before
it? (d) Minimum possible completion time. (e) Approximate time for repeated DCQCN halving to bring the
aggregate rate to the drain rate, and what fraction of (d) that is. (f) BDP, and a defensible upper
bound for Kmin.
*Evidence required:* six results with formula → substitution → result.

---

## Hands-on lab

**H1 ★★ L1 (L3 extension) — Progressive Lab 3: congestion telemetry diagnosis.** Complete
[lab/README.md](lab/README.md) Tasks 1–8 until `python check.py` reports every check PASS (or SKIP), then hand-edit the
generated report into the chapter deliverable: congestion diagnosis (ranked hypotheses and
discriminating evidence per episode), experiment plan, mitigation proposal.
*Evidence required:* checker output; report (≤ 3 pages) with every section in `REPORT_SECTIONS`; the
simulation table labelled `[SIMULATED]`; a "cannot conclude" list of at least four items.

---

## Course-outline exercises (mandatory)

**O1 ★★ L1 — Analyze a synthetic time series.** Analyze the lab's time series (queue depth, ECN marks,
CNPs, pause frames tx/rx, throughput, latency) and identify the likely congestion pattern of each
episode. For each, quote the two or three numbers (with units, from your rates) that most strongly
discriminate it from the alternatives.
*Evidence required:* per episode: label, root or source device, and the quoted discriminating values.

**O2 ★★ L1 — Why not PFC everywhere?** Explain why enabling PFC indiscriminately can create operational
risk. Then describe, as a numbered procedure an on-call engineer could follow, how you would
investigate pause propagation and head-of-line blocking on ORION using switch and NIC counters and
latency probes.
*Evidence required:* at least four distinct risks, each with its mechanism; a procedure of at least six
steps naming the counters read at each step and the decision rule applied.

**O3 ★★★ L1 (L3 to execute) — Controlled experiment.** Design a controlled experiment comparing
congestion behaviour under two documented configurations (choose: ECN thresholds as in the lab's A vs B,
or PFC on vs off with selective retransmission). State what cannot be concluded from the lab's
simulation, and what your experiment would and would not establish.
*Evidence required:* hypothesis; both configurations in full; workload; one controlled variable;
repetitions (≥ 5) and warm-up; metrics; analysis method; environment manifest fields; safety boundary;
a "cannot conclude" list of at least four items specific to the model.

---

## Troubleshooting case

**T1 ★★★ L1 — Lossless discards on one uplink.** Two days after rail leaf `orion-be-leaf-r5` was replaced,
the lossless-class discard alert fires (`[ILLUSTRATIVE]` evidence below). No other leaf has discards;
NCCL jobs on rail 5 show occasional retransmission-driven slowdowns. Spine-1 sits in the same network
rack as the leaf; spine-4 sits in the second network rack, across the hall.

```text
orion-be-leaf-r5, 5-minute window
port      peer                        length   pfc_tx/s   pfc_rx/s   q_tc3_wm_kb   discards_tc3 (5 min)
eth1/7    orion-n07 mlx5_5              30 m       820          0          410            0
eth1/33   orion-be-spine-1 eth1/41      20 m     2,880          0        2,090            0
eth1/57   orion-be-spine-4 eth1/41     100 m     2,950          0        2,120        1,214

orion-be-leaf-r5 buffer profile (all ports): lossless PG3 headroom computed for cable_length = 5m
```

(a) List and rank at least three hypotheses. (b) Compute the headroom the profile provides and the
headroom the 100 m uplink needs (port MTU 9,216 B, t_resp 1 µs), and the deficit. (c) Explain why
eth1/33 has the same pause rate but no discards, and say whether this evidence shows eth1/33 is safe.
(d) Propose a safe fix and validation.
*Evidence required:* ranked hypotheses with the evidence that discriminates them; two headroom values
and the deficit with arithmetic; the eth1/33 headroom calculation and an explicit statement of what
the evidence can and cannot prove about it; fix with change-control steps and validation criteria.

---

## Design challenge

**D1 ★★★ L1 — A second lossless class?** The Storage team wants its new RDMA-based checkpoint traffic
(Chapter 14) to share ORION's backend fabric as a *second* lossless priority (priority 4), arguing that
checkpoints "cannot tolerate loss". Write a one-page recommendation: accept, reject, or accept with
conditions. Quantify the headroom cost for a rail leaf (32 host ports at 30 m, 32 spine ports at 100 m),
explain the interaction with W-TRAIN's TC 3, and compare at least two alternatives.
*Evidence required:* headroom arithmetic; at least three risks; at least two alternatives in a
trade-off table; a decision with the conditions or evidence that would change it.

---

## Reflection and review

**R1 ★ L1.** The lab's model finds that the template ECN profile cuts pause exposure ≈ 7.6× but
lengthens incast completion ≈ 31 %. Which of these two numbers would you trust more on real hardware,
and why?

**R2 ★ L1.** The lab dataset is sampled every 2 s. Name two congestion phenomena from this chapter that
2 s sampling could hide completely, and the telemetry feature that would reveal each.

**R3 ★★ L1.** In the Section 9.12 scenario, what evidence *proves* the root cause, and what evidence is
merely correlated with it?

**R4 ★★ L1.** Your congestion-tree root finder relies on the rule "congested and not receiving pause".
Describe a situation where that rule would misidentify the root, and what extra evidence you would use.

*Evidence required (R1–R4):* a short paragraph each that names specific counters, assumptions, or
limitations from the chapter.
