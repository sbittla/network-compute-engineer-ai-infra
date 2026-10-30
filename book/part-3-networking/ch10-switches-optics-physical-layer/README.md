# Chapter 10 — Switches, Optics, Cabling, and Physical-Layer Operations

**Part III — Networking for AI Clusters · Course week 6 (with Chapter 9) · Progressive Lab 3
(physical-layer counters)**

A 256-GPU job is only as fast as its worst link, and in AI fabrics the worst link is usually dirty,
damaged, mis-seated, mis-patched, or the wrong part rather than congested. This chapter explains the
switch ASIC pipeline and shared buffer, how a 400G port is built from 100 Gb/s PAM4 lanes and
RS(544,514) FEC, the optics and copper options for AI back-ends, link-budget arithmetic, DOM and
error-counter interpretation, and — above all — how to separate physical-layer faults from
congestion and configuration problems that look like them. It closes with cleaning and inspection,
cabling schedules and labeling, commissioning, and sparing, all on the ORION reference cluster.

## Learning objectives

1. **Explain** the packet path through a switch ASIC and the cut-through vs store-and-forward trade-off.
2. **Explain** how a 400G port is built from PAM4 lanes, 256b/257b transcoding, and RS(544,514) FEC, and **calculate** line rate and FEC overhead.
3. **Compare** DAC, AEC, AOC, and pluggable optics (SR8, DR4, FR4) and select a medium per link class.
4. **Calculate** an optical link budget in dB/dBm and use it to interpret measured receive power.
5. **Interpret** DOM and CRC, symbol, FEC, and link-flap counters, and **diagnose** physical vs higher-layer causes.
6. **Design** a cabling schedule and labeling scheme, a commissioning checklist, and a sparing plan.
7. **Validate** a leaf switch's physical layer with an automated analyzer and produce a commissioning report.

## Prerequisites

Chapters 2, 3, 5, and 7 (fabric design, addressing, eBGP, ECMP, MTU). Read alongside Chapters 8 and 9.

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3.5 h |
| Exercises | 4 h |
| Lab (L1) | 3–4 h |
| L3 extension (optional, lab hardware) | 4 h |

## Lab tier

L1 (laptop, `[SIMULATED]` data). L2/L3 hardware extensions described in [lab/README.md](lab/README.md).

## Deliverable (course outline)

**Physical-layer runbook and port/cabling schedule** — Exercise 10.M4 in [exercises.md](exercises.md).

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Exercise set including outline-mandated 10.M1–10.M4 |
| [lab/README.md](lab/README.md) | Lab guide: link-health analyzer, commissioning report, BOM/spares, cabling schedule |
| `lab/manifest.yaml` | Environment manifest |
| `lab/data/` | Two-snapshot counter/DOM dataset, cabling schedule, thresholds, fabric specs |
| `lab/tools/` | Dataset generator — instructor copy only (stripped from the student release) |
| `lab/starter/linkhealth.py` | Learner module (TODOs) |
| `lab/check.py` | Checker: `python check.py [--impl starter|solution] [--report FILE]` |
| `solutions/` | Instructor answer key and reference implementation |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |
