# Chapter 21 — Exercise Answer Key (INSTRUCTORS ONLY)

All results `[MODELED]` from `[ILLUSTRATIVE]` inputs; arithmetic checked twice (by hand and with the
reference `capacity_model.py`).

## Knowledge checks

**K1.** Allocated = allocated GPU-h / usable GPU-h (scheduler). Active = GPU-h with kernels resident /
allocated GPU-h (`DCGM_FI_DEV_GPU_UTIL`). MFU = achieved model FLOP/s / peak FLOP/s. Goodput = GPU-h
producing retained progress / allocated GPU-h. `avg(DCGM_FI_DEV_GPU_UTIL)` approximates *active* (and,
averaged over all GPUs, mixes in idle and drained ones); it counts NCCL kernels waiting on the network
as busy, so it says nothing about efficiency.

**K2.** 1,024 × 0.96 × 0.95 × 0.92 = 1,024 × 0.839 = 859 usable GPUs.

**K3.** Stranded = installed (paid-for) capacity that cannot be used. Other causes: missing network
(leaf groups not cabled/validated — visible as nodes not in the scheduler or failing fabric tests);
nodes stuck in acceptance or repair (lifecycle state counts); a cooling limit (CDU capacity) forcing
nodes off; GPUs of the wrong type for the demand (inference-only pool, no training software support).

**K4.** Queueing delay rises without bound as utilization approaches 100 %; for gang jobs that need many
whole nodes at once, waiting for a large contiguous block takes far longer than the average utilization
suggests, so large jobs starve. Planning to ≤ 85 % keeps queues bounded and leaves room for failures and
fragmentation.

**K5.** 304.6 × 1.25 = 380.8 kW; 304.6 × 1.45 = 441.7 kW (+16 %). PUE says nothing about IT efficiency
(useful work per IT watt), varies with weather and load, and hides where the overhead goes (cooling vs
electrical losses). Common mistake: applying PUE to a figure that already includes it.

**K6.** (a) 65.55 × 0.9 = 59.0 kW: with 2N either side must carry the whole rack when the other side is
lost, so the plan is limited by one side (two circuits), then by the transient margin. A 4-node ORION
rack (40.8 kW max) fits easily. (b) 32.78 × 0.9 = 29.5 kW — two uncapped HX8 nodes (20.4 kW), or three
capped at ≤ 650 W (3 × 9.8 = 29.4 kW).

**K7.** 1,024 × (0.650 − 0.400) kW = 256 kW per step cycle. Mitigations: power caps (Platform), staged
job start/stop ramps (Training Infra), facility agreement on maximum step change and UPS/generator
sizing (Facilities).

## Worked problems

**W1.** Capex = $14.96M / 5 = $2.992M. Power = 32 × 8.5 × 1.12 × 1.25 × 8,760 × 0.12 = 304.64 kW × 1.25 ×
8,760 × 0.12 = $0.400M. Space = $0.570M (unchanged). Support = 0.08 × 14.96M = $1.197M. Staff = $0.960M.
Total = **$6.119M/yr**. Nominal $/GPU-h = 6.119M / 2,242,560 = **$2.73**. Allocated fraction = 0.850 ×
0.80 = 0.680 → $2.729 / 0.680 = $4.01; useful × 0.90 → **$4.46** per useful GPU-h. *Marking:* 1 pt per component, 2 per unit
cost. Common mistake: changing allocation in the usable fraction rather than after it.

**W2.** Budget = 30 × 0.9 = 27 kW per rack; node peak = 4.6 + 8 × cap.

| Cap | Node peak | Nodes/rack | Deployable (16 racks) | Throughput |
|---|---|---|---|---|
| 650 W | 9.8 kW | ⌊27 / 9.8⌋ = 2 | 32 | 32 × 0.990 = 31.7 |
| 550 W | 9.0 kW | ⌊27 / 9.0⌋ = 3 | 48 | 48 × 0.945 = 45.4 |
| 350 W | 7.4 kW | 3 | 48 | 48 × 0.700 = 33.6 |

(b) 550 W is best: it is the lightest cap that fits a third node. Going deeper (350 W) adds no node — a
fourth needs ≤ 6.75 kW, i.e. a cap ≤ 269 W — and only throws throughput away. (c) With 22 racks: at
550 W all 64 nodes fit (66 slots) → 64 × 0.945 = 60.5; at 650 W or uncapped only 2 per rack → 44 nodes
→ 43.6 / 44.0. Recommend 550 W on 22 racks; running all 64 uncapped would need 32 racks.
*Marking:* table 4, reasoning 3, recommendation 3. Common mistake: using the old 3.6 kW base.

## Hands-on lab — reference results and planted anomalies

| Output | Reference |
|---|---|
| Plan | 12 quarters after dropping the exact duplicate 2027Q3 row |
| Usable fraction / IT kW per GPU | 0.8496 (0.97 × 0.922 × 0.95) / 1.428 kW |
| Energizable GPUs (420 / 800 / 1,500 kW) | 288 / 560 / 1,048 |
| Stranded | 464 in 2028Q2–Q3; 232 in 2029Q2 |
| First shortfall | 2028Q3 (usable 475.8 < required 494.1); also 2029Q4 (870.0 < 964.7) |
| Order-by for 2028Q3 | GPUs 2028Q1; network 2028Q2; facility power 2027Q3 |
| ORION-256 TCO | $6.77M/yr (PUE 1.25); $3.02 nominal, $4.18 allocated, $4.75 useful per GPU-h |
| Designs (1.0 MW hall) | A 87 nodes, 442.3 units, 26.53/$M, 396/MW; B 62 nodes, 644.9 units, 31.36/$M, 645/MW |
| Power cap (legacy racks, 29.5 kW planned) | 700 W: 2/rack, 32.0, 9.1 kW unused per rack, 32 racks for all; 650 W: 3/rack, 47.52 (best); 4/rack would need ≤ 347 W |
| Flags | STRANDED_GPUS 2028Q2, 2028Q3, 2029Q2; RESERVE_SHORTFALL 2028Q3, 2029Q4; PER_GPU_COST_MISLEADS B |

**Planted anomalies (do not distribute):**
1. Exact duplicate 2027Q3 row — counting it adds 256 phantom GPUs and hides nothing else; the checker
   also verifies a *conflicting* duplicate raises.
2. 2028Q2 delivers 512 GPUs while facility phase 2 is only energized in 2028Q4 — 464 stranded.
3. 2028Q3 demand step (new pretraining program) makes the stranded quarter a shortfall while the nominal
   view shows 41 % "utilization".
4. 2029Q2 delivery exceeds the 1,500 kW hall (232 stranded) — the delivery was planned against GPU
   count, not power.
5. 2029Q3 retires 256 GPUs — supply falls while demand grows; 2029Q4 shortfall.
6. Design B is 1.73× the cost per GPU but 0.85× the cost per useful unit — per-GPU procurement metrics
   choose the wrong design.
7. Design B is power-bound (62 nodes), not cooling-bound (87) — learners who assume liquid cooling is the
   limit get the wrong node count.
8. The power-capping optimum (650 W, the lightest cap that fits a third node) is not the throughput-per-kW
   optimum (≈ 500 W) — the binding constraint is rack slots/circuits, not energy.
9. The legacy-hall case is a declared variation (one 32.78 kW circuit per side); canonical ORION racks have
   two per side (65.55 kW) and fit four uncapped nodes on one side.

**Marking:** see lab README rubric; deduct for any recommendation that does not name the binding
constraint, and for unlabeled numbers in the memo.

## Troubleshooting case T1

| Hypothesis | Evidence | Verdict |
|---|---|---|
| Rack planned against the *sum* of both sides (41 kW ≤ 2 × 32.78) instead of one side; with B down for maintenance the whole rack sat on one 32.78 kW circuit | Capacity-plan line; B de-energized 08:00–12:00; 41.6 kW peak on A | Root cause (condition) |
| Synchronized job start step | 12.1 → 41.6 kW within ≈ 3 s as all nodes ramp together; 41.6 kW ≈ 61 A per phase, far above the PDU's 48 A electronic overcurrent setting (not enough to trip the 60 A thermal-magnetic breaker in seconds) | Trigger |
| Faulty breaker | lh-04 (3 nodes) peaked at 30.9 kW on the same kind of circuit and held; main-hall racks have two circuits per side | Not supported (inspect anyway) |
| Node fault | All four nodes lost input simultaneously at the trip | Consequence |

Root cause (system): the legacy-hall capacity plan violated the 2N rule — a rack must fit on one side —
and the maintenance procedure did not check single-side loading before opening B. Immediate mitigation:
keep lh-03 at three nodes (or drained) until B returns; requeue the job from its checkpoint elsewhere.
Arithmetic: planned budget per side = 32.78 × 0.9 = 29.5 kW. Four nodes need ≤ 7.375 kW each → cap ≤
(7.375 − 4.6) / 8 ≈ 347 W, below the useful range of the curve (350 W ≈ 0.70 and still 29.6 kW). So the
guardrail is *three nodes per legacy rack at ≤ 650 W* (3 × 9.8 = 29.4 kW), enforced by the capacity plan,
plus an automated check before any single-side maintenance: "every rack's planned peak ≤ one side's
budget, else cap/drain first" (owners: Facilities for the signal, Platform for the action).
*Marking:* hypotheses 3, arithmetic 3, guardrail 3, blameless phrasing 1.

## Design challenge D1 — reference approach

Dedicated: 96 GPUs × 8,760 h = 840,960 GPU-h/yr; average load 40 % of peak → ≈ 505,000 GPU-h idle. Shared:
never lend the N+2 headroom (16 GPUs); lend idle replicas beyond a forecast-plus-margin threshold —
assume 60 % of the idle hours are lendable (≈ 300,000 GPU-h) at goodput 0.7 for preemptible jobs
(frequent checkpoints) → ≈ 210,000 useful GPU-h/yr ≈ $1.0M at $4.75 `[MODELED]`. SLO risk: reclaim must
finish (job checkpoint/kill + model reload) before traffic ramps; keep weights resident or use fast
reload; trigger reclaim on rising queue depth, not on breach. Guardrails: lending stops when forecast
peak − 30 min approaches; TTFT burn-rate alert inhibits lending; audit of reclaim times (p99 < 60 s).
Recommend shared with these guardrails if reclaim is measured < 60 s; otherwise dedicated.

## Reflection — guidance

- **R1:** Per-GPU throughput of the candidate design (benchmark), the power/throughput curve (L2
  measurement), and the fragmentation/allocation factors (scheduler telemetry over a quarter).
- **R2:** State B's break-even (≈ 1.86× per-GPU) and propose running W-TRAIN-like and inference
  benchmarks on B-class hardware with the Chapter 22 methodology before committing.
- **R3:** Financing, taxes/depreciation, resale, demand charges, software licences, data egress,
  decommissioning; financing and demand charges can change design decisions.
- **R4:** Facilities BMS/EPMS and PDU telemetry → a power-budget service consumed by the scheduler; owned
  jointly by Platform and Facilities with a defined interface.

## Outline-mandated exercises

- **M1 (P90, +25 % demand from 2028Q3):** shortfalls in 2028Q3 (usable 475.8 vs required 617.6, −141.9),
  2029Q2 (890.4 vs 925.9), 2029Q3 (870.0 vs 1,058.8), 2029Q4 (870.0 vs 1,204.7). The 2028Q3 cause is power
  (order by 2027Q3); the 2029 shortfalls need GPUs *and* power (1,048-GPU energizable limit) — order power
  by 2028Q2 and GPUs by 2028Q4 for 2029Q2. P50 shortfalls: 2028Q3 (−18.3), 2029Q4 (−94.7).
- **M2:** Table 21.3 plus sensitivity: B per-GPU throughput 1.8× → 25.7 units/$M (< A's 26.53); break-even
  ≈ 1.86×; if B's network does not scale with compute, efficiency ≈ 0.88 → ≈ 29.6/$M (still ahead). Electricity has small effect on per-$ ranking (≈ 4 % of TCO).
- **M3:** Expected rows: energized power (464 stranded), cooling (CDU-limited halls), maintenance (3 %),
  repair (7.8 % from the 5-day MTTR; spares outside the partition are extra capex), fragmentation (5 %), allocation headroom (85 %), goodput (81–88 %),
  network oversubscription (0.93 efficiency at 2:1), storage (checkpoint concurrency), onboarding (2–3
  weeks dock-to-schedulable; 95 % first-pass yield), inference pools sized for peak.
- **M4:** Design-B rack: 8 × 14.3 = 114.4 kW provisioned; 80 % to liquid = 91.5 kW → flow 91.5 / (4.18 ×
  10) = 2.19 kg/s ≈ 131 L/min water; residual air 22.9 kW. Hall 1.0 MW IT → 62 nodes ≈ 8 racks. Guardrails
  as Table 21.5 adapted (CDU supply temperature, pump redundancy, per-rack budget, feed loss cap). Hand-off
  checklist: rack weight and floor loading, coolant quality and filtration, leak detection and isolation
  valves, CDU redundancy mode, supply/return temperatures and ΔT, flow per rack, electrical circuits per
  feed and redundancy mode, metering and telemetry points, commissioning tests, maintenance access and
  ownership boundaries. Deduct for any rack-power figure not tied to a stated reference design.
