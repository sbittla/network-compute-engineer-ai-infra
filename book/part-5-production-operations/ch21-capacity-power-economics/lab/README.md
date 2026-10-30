# Lab 21 — Capacity Forecast, TCO, Design Comparison, and Power Capping

Tier **L1** (laptop). Evidence class: `[MODELED]`.

## 1. Goal and the real-world task it mirrors

Halcyon's leadership asks three questions every AI-infrastructure team answers each quarter: *When
do we run out of capacity, and what must we order by when? Which design should the next hall use?
Can we fit more GPUs into the halls we already have?* You will build the model that answers them,
and in doing so find the places where "we have N GPUs" is the wrong number:

1. clean the quarterly plan (it contains a data-entry duplicate);
2. forecast usable capacity per quarter from deliveries, decommissions, energized facility power,
   maintenance/repair/fragmentation reserves, and demand with allocation headroom; find the first
   shortfall and the order-by dates implied by lead times;
3. compute ORION-256's total cost of ownership and the cost per nominal, allocated, and useful
   GPU-hour;
4. compare two designs for a 1.0 MW hall on useful throughput per dollar and per watt;
5. model GPU power capping against rack power limits and transient headroom;
6. flag every case where the nominal GPU count misleads.

## 2. Tier and realism boundary

Pure modeling on illustrative inputs. It cannot tell you real prices, delivery dates, the real
power/throughput curve of your GPUs, or how your facility behaves under synchronized load swings —
those need quotes, vendor data, L2 measurements, and facilities engineers. Every output is `[MODELED]`.

## 3. Setup

```bash
cd book/part-5-production-operations/ch21-capacity-power-economics/lab
python -m pip install -r ../../../../requirements.txt
python check.py                     # progress on starter/capacity_model.py
```

## 4. Background

| Topic | Manuscript section |
|---|---|
| Utilization definitions, nominal vs usable capacity | 21.1–21.2 |
| Demand forecasting and lead times | 21.3 |
| TCO and cost per useful GPU-hour | 21.4 |
| Throughput per $ and per W; design comparison | 21.5 |
| Facility power, cooling, transients, power capping, guardrails | 21.6–21.8 |
| Worked example | 21.9 |

## 5. Data

| File | Contents |
|---|---|
| `quarterly_plan.csv` | 2027Q1–2029Q4: GPUs delivered/decommissioned, energized facility IT kW, training and inference demand (GPUs) |
| `assumptions.yaml` | Reserves, allocation target, goodput, node power, lead times, prices |
| `designs.yaml` | Design A (H100-class, air) and Design B (next-gen, liquid) for a 1.0 MW hall |
| `power_cap_curve.csv` | GPU power cap vs relative training throughput |
| `power_cap_case.yaml` | Declared variation: 64 nodes, 16 legacy-hall racks with one 32.78 kW circuit per side, 10 % transient margin, 4.6 kW node base |

## 6. Tasks

| # | Task | Functions | Acceptance criterion (checked) |
|---|---|---|---|
| 1 | Plan hygiene | `clean_plan` | Exact duplicates removed; conflicting duplicates raise |
| 2 | Forecast | `usable_fraction`, `it_kw_per_gpu`, `forecast`, `first_shortfall`, `order_deadlines` | Energized/stranded GPUs, usable vs required per quarter; first shortfall and order-by quarters |
| 3 | TCO | `tco` | ORION-256 annual TCO and $/GPU-h (nominal, allocated, useful) |
| 4 | Design comparison | `compare_designs` | Nodes per hall, useful throughput, per $M/yr, per facility MW |
| 5 | Power capping | `power_cap_tradeoff`, `best_cap` | Nodes per rack, cluster throughput, and unused (stranded) rack budget per cap; best cap |
| 6 | Misleading nominal counts | `misleading_nominal_flags` | Stranded-GPU (installed, not energized), reserve-shortfall, and per-GPU-cost flags |

ORION-256 TCO inputs for Task 3: 32 nodes at $320k, $85k network per node, $2.0M fixed storage capex
(`fixed_capex_usd`), staff from `assumptions.yaml`.

## 7. Running the checker

```bash
python check.py                    # starter
python check.py --impl solution    # instructors
```

## 8. Deliverable and grading rubric (100 points)

Submit `capacity_model.py` and a two-page **decision memo** (`decision_memo.md`) with an **assumptions
register** and **operational guardrails**.

| Item | Points |
|---|---|
| Tasks 1–2 correct; forecast chart or table; written order-by recommendation (what, how much, by when) | 25 |
| Task 3 correct; TCO breakdown table with each component's share; sensitivity to utilization and goodput (±10 points) | 15 |
| Task 4 correct; recommendation that states which constraint binds (power, cooling, capex) and the assumptions it depends on | 20 |
| Task 5 correct; rack-level guardrail proposal (cap, monitoring thresholds, who acts) | 15 |
| Task 6 correct; one paragraph per flag explaining to finance why nominal GPUs mislead | 10 |
| Assumptions register: every input with source/label, owner, and how it would be measured | 15 |

## 9. Extensions (L2 / L3)

> **Safety:** Changing GPU power limits is a system configuration change. Do it only on a dedicated
> lab host, restore the default afterwards, and never on shared or production nodes.

**L2 — measure your own power/throughput curve.**

```bash
nvidia-smi -q -d POWER                       # default, min, max, enforced power limits
sudo nvidia-smi -i 0 -pl 550                 # set a cap (lab host only; resets at reboot / driver reload)
nvidia-smi --query-gpu=index,power.draw,clocks.sm,clocks_event_reasons.sw_power_cap --format=csv -l 1
sudo nvidia-smi -i 0 -pl <default>           # restore
```

Run a fixed training-like benchmark (warm-up, then ≥ 5 runs per cap) at each cap from the curve and
record median and p95 step time and mean power. Replace `power_cap_curve.csv` with your measured
curve, labelled `[MEASURED]` with the manifest filled in.

**L3 — rack telemetry (read-only).** Pull 1 s (or finest available) rack-PDU power during a
multi-node training job and compute peak, p99, and the swing between compute and communication phases.
Compare with the `transient_margin` assumption.

## 10. Intentionally flawed inputs

The plan and designs contain planted traps (a duplicate row, deliveries ahead of energized power, a
retirement, a design whose per-GPU cost hides better economics, a constraint that binds before the
obvious one). They are documented for instructors in `../solutions/exercises-key.md`.
