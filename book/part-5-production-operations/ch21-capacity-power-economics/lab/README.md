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

Lead times in `assumptions.yaml` run from order to *in service*; `onboarding_quarters` (0 here) adds
dock-to-schedulable time when your quotes are order-to-dock, and `order_deadlines` subtracts both.
The checker prints `hint:` lines when it recognizes a common mistake (a counted duplicate row, usable
capacity computed from installed GPUs, a missing transient margin, and others).

ORION-256 TCO inputs for Task 3: 32 nodes at $320k, $85k network per node, $2.0M fixed storage capex
(`fixed_capex_usd`), staff from `assumptions.yaml`.

## 7. Running the checker

```bash
python check.py                    # starter
python check.py --impl solution    # instructors
```

## Troubleshooting

- **`ModuleNotFoundError` naming `numpy`, `pandas` or `yaml`** (as a traceback, or on a
  `FAIL import/load` line). Install the
  requirements into the interpreter you run `check.py` with: `python -m pip install -r
  ../../../../requirements.txt`. Use Python 3.10 or newer (`python --version`).
- **`FAIL import/load: SyntaxError(...)` and no other lines.** The checker could not import
  `starter/capacity_model.py`, so it ran nothing. `python -m py_compile starter/capacity_model.py`
  prints the file and line.
- **Every line says `TODO ...: implement <name>()`.** That is the expected start: each function still
  raises `NotImplementedError`. A line turns into `PASS` or `FAIL` once that function returns.
- **A `FAIL` line names an exception but not where it happened.** Rerun with `python check.py -v`,
  which prints the full traceback for each failing check.
- **`check_reproducible` FAILs with `<file> differs from regenerated copy`** (instructor copy only; it
  is a `SKIP` in the student release). A file in `data/` has been edited. Restore it with
  `git checkout -- data/` and put your own scenarios in a copy instead.
- **`--impl solution` gives `FAIL import/load: FileNotFoundError(...)`.** The reference
  implementation is instructor material and is removed from student releases. Run `python check.py`
  without the flag.

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

**L2 on any single GPU (scripted, with CPU fallback).** The cap sweep above needs root on a dedicated bare-metal
host. `lab/l2/experiment.py` never changes a power limit. It reads the default, enforced, minimum and maximum
limits and records the cap sweep as not runnable when it cannot be done (for example under WSL2 or without root).
It then measures what one GPU can show at its default limit: a compute-bound FP16 GEMM duty-cycled at 0, 25, 50,
75 and 100 %, plus a memory-bound copy. For each level it records power sampled every 100 ms (mean, p5/p95,
swing), throughput, SM clock, temperature and `SW_POWER_CAP` share, then derives perf/W, energy per TFLOP and a
linear power model. It puts the result next to the lab's `power_cap_tradeoff` on `power_cap_curve.csv`.

```bash
python scripts/hw_labs.py build ch21
python scripts/hw_labs.py run ch21 --device gpu   # needs the NVIDIA container runtime
python scripts/hw_labs.py run ch21 --device cpu   # throughput vs duty on the CPU; perf/W not runnable (no RAPL)
```

Without a GPU (`--device auto` on a host with no NVIDIA driver) the CPU fallback runs automatically. It runs the
same sweep with throughput and CPU busy time. Host power is not readable, so perf/W is recorded as not runnable,
and the lab's modeled cap curve stands in. GPU-only invariants are skipped.

**Observed on the reference run** `[MEASURED]`, RTX 4060 Laptop GPU under WSL2 (`lab/l2/results/gpu-rtx-4060-laptop-gpu/`;
invariants pass):

- At clock-matched duty levels perf/W rises with duty: 0.264 TFLOP/J at 50 %, 0.298 at 75 % and 0.341 at 100 %.
  Static power is paid whether or not work runs.
- The 25 % level ran at a 300 MHz SM clock (DVFS idled the GPU between bursts), so the report marks light duty
  inconclusive rather than drawing a duty-cycling conclusion from it. Locking clocks on a dedicated native-Linux
  lab host (root) would test it.
- Full-load GEMM drew 75.65 W against the 80 W enforced limit, with `SW_POWER_CAP` in only 30 % of samples at
  88 °C: temperature, not the power cap, set the clock. The memory-bound copy ran at 2,520 MHz and 52.45 W.
- The CPU-fallback bundle records throughput and CPU busy time only; host power is not readable there.

The report was re-rendered from its committed `results.json` with the current `experiment.py`; no measured value
changed, and the original evaluation is kept under `invariants_history`. These are laptop watts. Do not put them
into the rack model.

**L3 — rack telemetry (read-only).** Pull 1 s (or finest available) rack-PDU power during a
multi-node training job and compute peak, p99, and the swing between compute and communication phases.
Compare with the `transient_margin` assumption.

## 10. Intentionally flawed inputs

The plan and designs contain planted traps (a duplicate row, deliveries ahead of energized power, a
retirement, a design whose per-GPU cost hides better economics, a constraint that binds before the
obvious one). They are documented for instructors in `../solutions/exercises-key.md`.

## Hands-on lab (single machine)

`handson/` runs one fixed training job on a real GPU (WSL2 works) at batch 1, 4 and 16 and at 75, 50 and
25 % busy, and integrates board power over time for energy per token and per FLOP. It then runs Section
21.4's cost-per-useful-GPU-hour ladder on your measured power and goodput beside ORION's $3.00. Where
power-limit changes are refused (WSL2) it records the refusal; on a dedicated Linux host an opt-in cap sweep
runs and restores the limit. See [handson/README.md](handson/README.md); the reference evidence is in
`handson/results/wsl2-rtx4060-laptop/`.
