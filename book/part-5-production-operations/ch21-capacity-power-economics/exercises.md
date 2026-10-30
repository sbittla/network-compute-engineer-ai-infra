# Chapter 21 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/paper · L2 one GPU host
· L3 lab rack with PDU telemetry. All inputs are `[ILLUSTRATIVE]` unless stated; all results `[MODELED]`.
Answers: `solutions/exercises-key.md`.

**Chapter deliverable (course outline):** a **capacity model** and a **cost/performance decision memo**
(M1–M3 / Lab 21), plus the Section 20.3 / table-8 evidence: a **capacity/power/cooling model and
operational guardrails** (M4).

---

## Knowledge checks

**K1 ★ L1 — The ladder.** Define allocated, active, MFU, and goodput utilization. Which one does
`avg(DCGM_FI_DEV_GPU_UTIL)` approximate, and why is it a poor efficiency measure?
*Evidence required:* four definitions with numerator/denominator; one-sentence mechanism.

**K2 ★ L1 — Usable capacity.** With maintenance 4 %, repair/spares 5 %, fragmentation 8 %, how many usable
GPUs does an energized 1,024-GPU cluster have?
*Evidence required:* formula, substitution, result.

**K3 ★ L1 — Stranded GPUs.** Define stranded capacity. Give two causes other than missing facility power.
*Evidence required:* definition; two causes with the telemetry that reveals each.

**K4 ★★ L1 — Why plan to 85 %?** Explain why a shared training cluster should not plan to 100 % allocation.
*Evidence required:* queueing argument; consequence for gang-scheduled jobs.

**K5 ★ L1 — PUE.** ORION-256's sustained IT load is 304.6 kW (32 × 8.5 kW × 1.12). What is the facility
power at the canonical PUE 1.25 and at 1.45 (a hot-season variation)? What does PUE not tell you?
*Evidence required:* two results; two limitations.

**K6 ★★ L1 — 2N feeds.** (a) An ORION rack has A and B sides of two canonical circuits each (32.78 kW
continuous per circuit, 65.55 kW per side). What is the maximum planned rack load with a 10 % transient
margin, and why? (b) Repeat for a legacy rack with one circuit per side.
*Evidence required:* two numbers and the failure scenario that sets them.

**K7 ★★ L1 — Transients.** Estimate the synchronized power swing of a 1,024-GPU job whose GPUs move between
650 W and 400 W each step. Name two mitigations.
*Evidence required:* arithmetic; two mitigations with owners.

## Worked problems

**W1 ★★ L1 — TCO under different assumptions.** Recompute ORION-256's TCO (Section 21.4) with 5-year
amortization, PUE 1.25, electricity $0.12/kWh, allocation 0.80, and goodput 0.90 (other inputs
unchanged). Report the annual total and the cost per nominal and per useful GPU-hour.
*Evidence required:* every component with formula; the two unit costs.

**W2 ★★★ L1 — Capping in a tighter hall.** Same 64 nodes and 16 racks as Section 21.8, but the rack limit is
30 kW (10 % transient margin) and you may only use the caps in the lab's curve; node peak = 4.6 kW + 8 × cap.
(a) Find nodes per rack and cluster throughput for 650 W, 550 W, and 350 W. (b) Which is best, and why is
"cap deeper to fit more nodes" not always right? (c) If six more racks become available (22 in all), what
do you recommend?
*Evidence required:* table for the three caps; reasoning; recommendation with numbers.

## Hands-on lab

**L1 ★★ L1 — Lab 21** ([lab/README.md](lab/README.md)). Implement `lab/starter/capacity_model.py`, pass
`python check.py`, and write the decision memo with assumptions register and guardrails.
*Evidence required:* 9/9 PASS; `decision_memo.md` per the lab rubric.

## Troubleshooting case

**T1 ★★ L1 — The breaker that tripped at job start.** *Declared variation:* Halcyon's legacy expansion hall
(Section 21.8) has racks with **one** canonical circuit per side (32.78 kW continuous, 2N A/B). At 09:02 rack
lh-03 (expansion nodes orion-n37 to orion-n40) loses its A side when a 32-node job starts. Evidence
`[ILLUSTRATIVE]`:

```text
capacity plan for lh-03: 4 HX8 nodes, "41 kW max <= 2 x 32.78 kW available"
change calendar: 08:00-12:00 UPS-B maintenance (legacy hall) - all B sides de-energized
lh-03 PDU-A (circuit continuous 32.78 kW = 48 A; PDU electronic overcurrent protection set at 48 A):
      08:55 load 12.1 kW (4 idle nodes) -> 09:02:10 41.6 kW (~61 A/phase) -> PDU overcurrent trip at 09:02:12
job start: 32 nodes ramp from idle to full training power within ~3 s (synchronised first step)
node BMC: 4 x "PSU input lost" at 09:02:11 ; GPUs at 700 W default limit
rack lh-04 (3 nodes): peak 30.9 kW on its A circuit, no trip
main-hall racks (two circuits per side, 65.55 kW): peaks 39-41 kW on side A, no trip
```

Walk the diagnostic loop: hypotheses, discriminating evidence, root cause (system, not person), immediate
mitigation, and the guardrail that would have prevented it (with the cap value computed).
*Evidence required:* hypothesis table; arithmetic for the cap; guardrail statement with trigger and owner.

## Design challenge

**D1 ★★★ L1 — The inference pool.** `chat-70b` needs 96 GPUs (Section 21.3) sized for peak + N+2, with average
load 40 % of peak. Option 1: dedicated pool. Option 2: shared pool where preemptible training borrows idle
replicas and must yield within 60 s. Compare useful GPU-hours per year, risk to the TTFT SLO, and
operational complexity. Recommend, with the guardrails that make your choice safe.
*Evidence required:* quantified comparison with assumptions; SLO risk analysis; guardrails.

## Reflection / review

**R1 ★ L1** — Which three inputs in your lab model would you most want measured rather than assumed, and
how would you measure each?

**R2 ★★ L1** — The design comparison treats B's 2.2× per-GPU throughput as known. Write the paragraph of
your memo that explains the break-even and the experiment that resolves it.

**R3 ★ L1** — Which costs are missing from the TCO model, and which could change a decision?

**R4 ★★ L1** — Where in your organisation would the facility → scheduler signals of Section 21.8 come from,
and who would own the integration?

*Evidence required (R1–R4):* concise answers citing sections or data files.

## Outline-mandated exercises

**M1 ★★ L1 — Capacity forecast.** Build a capacity forecast from **accelerator supply, workload demand,
utilization, maintenance reserve, and expected growth** (lab Tasks 1–2) and extend it with a P90 demand
scenario (+25 % demand from 2028Q3). Report the first shortfall quarter and order-by dates for each
scenario.
*Evidence required:* forecast table for both scenarios; order-by dates; the binding resource per shortfall.

**M2 ★★ L1 — Two designs.** Compare two cluster designs on **useful throughput per dollar and per watt** using
explicit assumptions (lab Task 4), add a sensitivity analysis on per-GPU throughput and electricity price,
and state the break-even.
*Evidence required:* comparison table; sensitivity table; break-even arithmetic.

**M3 ★★ L1 — Misleading nominal counts.** Identify the **bottlenecks that make nominal GPU count a misleading
measure of usable capacity** — at least six, including power, cooling, maintenance and failure reserves,
fragmentation, network oversubscription, storage, and onboarding — with a quantified ORION or ORION-XL
example of each (lab Task 6 covers three).
*Evidence required:* table: bottleneck, mechanism, example number, telemetry that reveals it.

**M4 ★★★ L1 — Capacity/power/cooling model and guardrails (Section 20.3, table 8).** For a hall of Design-B
racks (8 nodes, 14.3 kW provisioned per node, 80 % heat to liquid), state the facility capacity, rack power
limit and redundancy mode, liquid-cooling capacity and required coolant flow at ΔT = 10 K, transient
headroom, and the power-capping policy. Produce the guardrail table (signal, threshold, automated action,
owner) and the workload/facility coordination interface.
*Evidence required:* assumptions register; rack power budget; coolant-flow arithmetic; guardrail table;
facility/MEP hand-off checklist (≥ 8 items).
