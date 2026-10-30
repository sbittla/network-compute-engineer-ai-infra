# Chapter 21 — Capacity, Power, and Infrastructure Economics

**Part V — Operating Production AI Infrastructure · Course week 13**

Nominal GPU count is an input, not an answer. This chapter turns installed GPUs into usable and useful
capacity (maintenance, repair/spares, fragmentation, energized power, network, storage, onboarding),
forecasts shortfalls and order-by dates from lead times, computes TCO down to the cost per useful
GPU-hour, compares designs on useful throughput per dollar and per watt, and treats the facility —
power chain, rack limits, liquid cooling, transient headroom, power capping — as a capacity constraint
with operational guardrails.

## Learning objectives

1. **Distinguish** allocated, active, MFU, and goodput utilization; **compute** the utilization ladder.
2. **Calculate** usable capacity from nominal capacity and its constraints.
3. **Build** a quarterly capacity forecast and **derive** order-by dates.
4. **Compute** TCO and cost per nominal, allocated, and useful GPU-hour.
5. **Compare** designs on useful throughput per dollar and per watt.
6. **Explain** facility constraints and **model** the power-capping trade-off.
7. **Define** workload/facility guardrails.

## Prerequisites

Chapters 2, 6, 7, 14, 15, 17, 18, and 19.

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3 h |
| Exercises | 3 h |
| Lab (L1) | 3 h |
| L2/L3 extension (optional) | 2–4 h |

## Lab tier

**L1** (`[MODELED]`); optional **L2** (measure a power-cap curve on a lab GPU) and **L3** (read-only rack
PDU telemetry).

## Deliverable (course outline)

Capacity model and cost/performance decision memo (M1–M3, Lab 21), plus the capacity/power/cooling model
and operational guardrails (M4, Section 20.3 / table 8).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Exercises including outline-mandated M1–M4 |
| [lab/README.md](lab/README.md) | Lab guide |
| `lab/data/` | Capacity plan, assumptions, designs, power-cap curve and case (`lab/tools/` generator: instructor copy only) |
| `lab/starter/capacity_model.py` | Learner module |
| `lab/check.py`, `lab/manifest.yaml` | Checker and environment manifest |
| `solutions/` | Answer key and reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |

## Connections

Uses Chapter 17 (fragmentation), Chapters 18–19 (goodput, spares), and Chapter 15 (inference capacity);
feeds Chapter 22, Chapter 23, and Capstones A and D.
