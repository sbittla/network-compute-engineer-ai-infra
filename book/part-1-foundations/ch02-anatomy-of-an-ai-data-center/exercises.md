# Chapter 2 — Exercises: Anatomy of an AI Data Center

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/paper · L2 single GPU
server · L3 multi-node or facility access. Every exercise states the **evidence required** for
grading. Unless an exercise says otherwise, use the ORION values in `docs/REFERENCE_CLUSTER.md` and
the assumptions of [manuscript.md](manuscript.md) Sections 2.2–2.10, and label every number you
produce `[MODELED]`, `[MEASURED]`, or `[ILLUSTRATIVE]`.

| # | Exercise | Type | Difficulty | Tier | Source |
|---|---|---|---|---|---|
| 2.1 | Knowledge check | Knowledge check | ★ | L1 | Standard set |
| 2.2 | Small-cluster servers, rack units, ports, and links | Worked problem | ★★ | L1 | Outline §14, exercise 1 |
| 2.3 | Simplified capacity model | Worked problem | ★★ | L1 | Outline §14, exercise 2 |
| 2.4 | ORION capacity, BOM, power, and SPOF lab | Hands-on lab | ★★ | L1 (+L2/L3 ext.) | Standard set; chapter deliverable |
| 2.5 | Five single points of failure | Design analysis | ★★ | L1 | Outline §14, exercise 3 |
| 2.6 | What liquid cooling does to node power and rack density | Worked problem | ★★ | L1 | Manuscript Section 2.7 |
| 2.7 | The maintenance-window slowdown | Troubleshooting case | ★★★ | L1 | Standard set |
| 2.8 | Power-cap sweep on one GPU server | Measurement | ★★★ | L2 | Manuscript Section 2.6 |
| 2.9 | High-density rack power and heat-removal budget with MEP handoff | Design challenge | ★★★ | L1 | Outline §20.3 exercise |
| 2.10 | Growing ORION to 512 GPUs in the same hall | Design challenge | ★★★ | L1 | Standard set |
| 2.11 | Reflection and review | Reflection | ★–★★ | L1 | Standard set |

---

## Exercise 2.1 — Knowledge check ★ · L1

Answer each in two to four sentences.

1. Why is an ORION GPU rack described as *power-limited, not space-limited*? Give the numbers.
2. Name the three networks in an AI cluster and state, for each, what a total failure of that network
   does to a running training job.
3. A rack has 2N feeds, each with two 60 A, 415 V three-phase circuits. What is the rack's usable
   capacity, and why is it not the sum of both sides?
4. What is the difference between TDP and the peak power a GPU can draw? Which part of the power
   chain absorbs microsecond excursions, and which part sees step-boundary swings?
5. Define the FWS, the TCS, and the CDU's approach temperature. Explain how a hot afternoon can slow a
   GPU in a liquid-cooled rack.
6. `nvidia-smi -q -d PERFORMANCE` shows `SW Power Cap: Active` on a GPU running a dense GEMM. Is that a
   fault? What would make it one?
7. Distinguish allocation, MFU, and goodput. Why do they multiply?
8. Give two reasons the optics count in a BOM matters operationally, not just financially.

**Evidence required:** written answers; numeric answers show formula → values → result with units.

---

## Exercise 2.2 — Small-cluster servers, rack units, ports, and links ★★ · L1

*(Outline-mandated: estimate the number of GPU servers, rack units, network ports, and fabric links
for a small cluster using stated assumptions.)*

Halcyon wants a 128-GPU cluster, **ORION-128**, from HX8 nodes, in an older hall. Assumptions
`[ILLUSTRATIVE]`:

- HX8 as in Chapter 2: 8 GPUs, 8U, 10.2 kW maximum; rack auxiliary load 0.2 kW.
- Rack circuits: 415 V three-phase, **32 A**, two circuits per side, 2N A/B; derate 0.80; power factor
  0.95; transient margin 10 %. 48U racks.
- Backend: rail-optimized, 8 rails, 400 Gb/s, 64-port leaves, 1:1; spines of 64 ports; every leaf has
  the same number of uplinks to every spine.
- Frontend: 2 × 200 Gb/s per node. OOB: one 1 GbE port per node BMC, per switch (backend and two
  frontend leaves), per storage server (4), and per rack PDU (4 PDUs per GPU rack).

Tasks:

1. How many nodes fit per GPU rack electrically? How many GPU racks are needed, and how many rack
   units do nodes occupy per full rack?
2. How many rail leaves and spines are required? How many host-to-leaf and leaf-to-spine links? How
   many switch ports are used and how many are left unused on the leaves?
3. How many single-port 400G transceivers are needed if every link is optical?
4. What is the bisection bandwidth per direction?
5. How many frontend node ports and OOB ports are required?
6. State one assumption you would most want to verify before ordering, and why.

**Evidence required:** a BOM table (item, quantity, formula); the per-side power calculation; a
one-line justification for the spine count.

---

## Exercise 2.3 — Simplified capacity model ★★ · L1

*(Outline-mandated: build a simplified capacity model that includes accelerator count, usable GPU
memory, storage throughput, network bisection bandwidth, power, and utilization.)*

Extend ORION-128 from Exercise 2.2 with these assumptions `[ILLUSTRATIVE]`: 10 % of each GPU's 80 GB
reserved for runtime and fragmentation; workload is a 13 × 10⁹-parameter dense model trained with
16 B/param of training state, TP = 8, PP = 1, and a 14 B/param checkpoint; storage is 4 servers at
20 GB/s read and 10 GB/s write each; non-GPU racks draw 10.0 kW (network), 4.5 kW (storage), and
3.0 kW (management) at maximum; PUE 1.30; allocation target 80 %; MFU 38 %; goodput 92 %.

Build the model as a spreadsheet or a short Python script and report:

1. Accelerator count, total and usable HBM (GB), and per-GPU training state (GB). Does the state fit?
2. Aggregate storage read and write (GB/s), read per GPU, and the lower-bound checkpoint write time.
3. Bisection bandwidth per direction (from Exercise 2.2).
4. IT maximum power (kW) and facility power at the stated PUE.
5. Allocated GPU-hours per year and the fraction of peak capability that becomes durable progress.
6. Which resource would you expect to bind first if the team doubled the model size? Justify.

**Evidence required:** the model file or table with formulas visible; every output labelled
`[MODELED]`; a three-sentence interpretation.

---

## Exercise 2.4 — ORION capacity, BOM, power, and SPOF lab ★★ · L1 (L2/L3 extensions)

Complete the [Chapter 2 lab](lab/README.md): implement `validate_inputs`, `compute_bom`,
`compute_power_cooling`, `compute_capacity`, `failed_set`, and `find_spofs` in
`lab/starter/capacity_model.py` until `python check.py` reports 14/14.

**Evidence required:** `check.py` output; the written deliverable from lab/README.md Section 7 (BOM
table, capacity spreadsheet, findings list with one consequence sentence per finding, failure-domain
diagram with mitigations and accept/fix decisions). For an L2/L3 extension, add a filled-in copy of
`lab/manifest.yaml` and raw measurement files.

---

## Exercise 2.5 — Five single points of failure ★★ · L1

*(Outline-mandated: identify at least five single points of failure in a sample cluster design and
propose mitigations.)*

**VEGA** is a 64-GPU inference cluster (8 HX8 nodes) a contractor proposed for Halcyon. Design notes
`[ILLUSTRATIVE]`:

- Two GPU racks of 4 nodes, each with A and B rack PDUs from separate UPS systems. One network rack
  with a single rack PDU on feed A.
- One sidecar liquid-to-air CDU per GPU rack.
- Frontend: each node dual-homed to two leaves (MLAG pair) in the network rack; one border router; a
  single hardware load balancer in front of the inference service.
- Model weights served from one NFS server; nodes fetch weights at pod start.
- Kubernetes control plane: three VMs on one hypervisor host in the network rack.
- DNS and NTP: one VM on the same hypervisor host.
- OOB: one 1 GbE switch for all BMCs and PDUs.

Tasks: (1) identify at least five SPOFs, stating the service impact of each; (2) draw the
failure-domain diagram; (3) propose a mitigation for each and decide fix or accept, with a reason
that refers to cost, likelihood, or recovery time; (4) identify one dependency that is a SPOF only
because of *where* something is placed or plugged, not because of how many there are.

**Evidence required:** SPOF table (component, impact, mitigation, fix/accept, reason); failure-domain
diagram; answer to task 4.

---

## Exercise 2.6 — What liquid cooling does to node power and rack density ★★ · L1

The DLC variant of HX8 replaces most fan power with pumps in the CDU. Assume `[ILLUSTRATIVE]`: peak
fan power falls from 1,350 W to 350 W; all other DC loads and the 94 % PSU efficiency are unchanged;
the liquid capture fraction becomes 80 % of node AC power; node weight is unchanged (135 kg); the
non-node rack mass is 280 kg. Use ORION's facility envelope (Section 2.10).

1. What is the DLC node's AC maximum? How much does a 4-node rack save?
2. Does a **fifth** node per rack fit electrically (per side, with 10 % transient margin)?
3. For a 5-node rack: coolant flow (PG25, ΔT 10 K), residual airflow (ΔT 15 K), and the load on a
   single 300 kW CDU serving 8 such racks.
4. Does the 5-node rack pass the 1,200 kg/m² floor rating?
5. Does the DLC node still have the feed-loss problem of Section 2.2?
6. Verdict: 4 or 5 nodes per rack? Name the binding constraint.

**Evidence required:** all arithmetic shown; a five-row check table (electrical, liquid, CDU, floor,
feed loss) with ✓/✗.

---

## Exercise 2.7 — The maintenance-window slowdown ★★★ · L1

During a planned two-hour UPS-B maintenance window (feed B de-energised by Facilities), W-TRAIN's step
time rose from 17.4 s to 22.6 s. After feed B returned, step time recovered. Evidence available so
far `[ILLUSTRATIVE]`:

```text
DCGM, during the window (per-rack medians)
rack    sm_clock_mhz  power_w  clock_event_reasons_active
rack-01  1755          655      none
rack-02  1050          330      HW Slowdown, HW Power Brake Slowdown
rack-03  1050          332      HW Slowdown, HW Power Brake Slowdown
rack-04  1755          652      none
rack-05..rack-08 (all)  1755  650-657  none

Rack PDU feed A, during the window
rack    feed_A_kw   breaker_events
rack-01  34.0        none
rack-02  24.1        none
rack-03  24.3        none
rack-04  33.8        none
```

Nobody has yet looked at the nodes' power-supply inventory or the PDU outlet maps.

Tasks:

1. Compute the slowdown and explain why 8 of 32 nodes slowed the whole job by that much.
2. Rank at least three hypotheses for why only rack-02 and rack-03 braked when the other racks, on the
   same feed A, did not.
3. List the discriminating evidence you would collect next, with the exact read-only commands or data
   sources, and what result would confirm or reject each hypothesis.
4. Assume the evidence shows that every node in rack-02 and rack-03 has two PSUs corded to feed A and
   four to feed B. Explain the braking with arithmetic, propose the safe fix, and say how you would
   validate it *without* waiting for the next maintenance window.
5. What change to the node acceptance checklist (Chapter 16) prevents a recurrence?

**Evidence required:** slowdown arithmetic; ranked hypothesis table; evidence plan with commands;
root-cause arithmetic; fix and validation plan; one acceptance-checklist line.

---

## Exercise 2.8 — Power-cap sweep on one GPU server ★★★ · L2

> **Safety:** Only on a dedicated server you are authorised to reconfigure. Restore default power
> limits afterwards and record that you did.

On one GPU, run a fixed workload (for example a large BF16 GEMM loop or an approved burn-in tool) at
power limits from the maximum down to roughly 55 % of it in about 50 W steps (`sudo nvidia-smi -i 0
-pl <W>`). At each step: 2-minute warm-up, then 5 repetitions of a 60-second measurement, sampling
`nvidia-smi --query-gpu=power.draw,clocks.sm,temperature.gpu --format=csv -l 1`. Plot throughput,
average power, and throughput per watt against the limit.

1. At what limit does throughput per watt peak? How much throughput is lost at that point?
2. Repeat with a memory-bound workload (large element-wise copy). How does the curve change, and why?
3. Using your curve, what fleet-wide limit would you propose as ORION's feed-loss policy
   (Section 2.10), and what would it cost the W-TRAIN step time if it were applied continuously?

**Evidence required:** filled-in `lab/manifest.yaml` copy (GPU model, driver, default limit, workload
definition, warm-up, repetitions); raw CSV; plot; median and spread per step; explicit
`[MEASURED]` versus `[MODELED]` labels for the answer to question 3.

---

## Exercise 2.9 — High-density rack power and heat-removal budget with MEP handoff ★★★ · L1

*(Outline §20.3 exercise.)* Halcyon is evaluating a hypothetical rack-scale accelerator system,
**Rack-X**, for a future cluster. Treat all figures as assumptions, not as a description of any
product. If you substitute a real vendor's rack-scale design, cite the vendor reference design by
title and the month you checked it; never present its figures as a universal rack standard.

Assumptions `[ILLUSTRATIVE]`: maximum IT load 120 kW per rack; transient margin 15 %; 2N A/B feeds;
415 V three-phase circuits; derate 0.80; power factor 0.95; liquid capture fraction 85 %; TCS coolant
PG25 (cp 3.90 kJ/(kg·K), ρ 1.02 kg/L) with ΔT 8 K and supply 30 °C; air ΔT 15 K (cp 1.006, ρ 1.20);
8 racks per row served by CDUs of 1 MW liquid capacity each; rack mass 1,400 kg on a 0.6 m × 1.2 m
footprint; floor rated 1,200 kg/m² over the footprint.

Produce:

1. **Power one-line concept** from utility to rack power shelves, showing redundancy at each stage.
2. **Rack electrical budget:** per-side design load; the number of 125 A circuits per side, and
   alternatively 160 A circuits, needed; PDU (or power-shelf input) headroom for your choice.
3. **Transient margin check:** if all 8 racks step by 30 % of maximum within 50 ms, what is the row's
   step in kW, and which stages of the chain must be confirmed against it?
4. **Thermal/cooling block diagram** (FWS, CDU, TCS, manifolds, cold plates, air path).
5. **Heat-removal budget:** heat to liquid and air per rack; coolant flow (L/min) per rack and per
   row; residual airflow (CFM) per rack; CDU count for N+1 at the row level and its utilization.
6. **Floor loading** and what you would ask the structural engineer.
7. **Safe operating envelope:** a table of the parameters operators must keep inside limits (per-side
   kW, TCS supply temperature, flow per rack, ΔT, CDU utilization, inlet air temperature), with the
   limit and the action when exceeded.
8. **Assumptions register:** every assumption, its value, its source (or "to be confirmed by"), and
   the consequence if it is wrong.
9. **Facility/MEP handoff checklist:** the items IT must give Facilities and receive from Facilities
   before installation (at least 12 lines), each with an owner.

**Evidence required:** the nine artefacts above; arithmetic for 2, 3, 5, and 6; each number labelled.

---

## Exercise 2.10 — Growing ORION to 512 GPUs in the same hall ★★★ · L1

Halcyon wants to double ORION to 64 HX8 nodes in the same row space, adding at most 6 racks. The
hall can supply up to 800 kW of IT load to the row, one additional 300 kW CDU, and no structural
work this year.

Choose and defend a design: rack count and nodes per rack (air-cooled HX8 or the DLC variant of
Exercise 2.6), CDU topology, backend fabric change (the current spines have no free ports), and how
you will remove the SPOFs found in the lab. Present a one-page decision record: options considered
(at least three), criteria, the decision, what you gave up, and the evidence you would collect before
committing.

**Evidence required:** decision record; power, cooling, CDU, and floor arithmetic for the chosen
option; the fabric change with switch and link counts.

---

## Exercise 2.11 — Reflection and review ★–★★ · L1

1. Which number in Section 2.10's fit assessment are you least confident in, and what measurement
   (tier and command) would replace it?
2. The lab treats a rail-leaf failure as a SPOF for full-scale training. Argue for or against
   accepting that risk, given what you know about restart cost.
3. What can the Chapter 2 lab *not* tell you about whether ORION will run well in the offered row?
4. Your Facilities colleague says, "PUE is 1.25, so efficiency is fine." What is missing from that
   statement for an AI cluster?
5. Which of the ownership cells in Table 2.7 has the highest risk of being nobody's job in your own
   organisation, and how would you fix that?

**Evidence required:** written answers, one paragraph each.

---

## Chapter deliverable

From the course outline: **cluster bill of materials, capacity spreadsheet, and failure-domain
diagram** — plus, from the definitive-edition enhancement for this chapter, the **rack power/thermal
budget and facility interface diagram**. Submit Exercise 2.4 (lab deliverable) and Exercise 2.9
together. Every number is labelled; every assumption is in the register.
