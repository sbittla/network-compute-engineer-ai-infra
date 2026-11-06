# 7.R4 — Modeled, simulated and illustrative numbers (model answer)

Relies on the evidence-label conventions (docs/STYLE_GUIDE.md §3) and the labelled numbers in
manuscript Sections 7.6, 7.9 and 7.12.

| Label | Example from the chapter | What it rests on | Measurement that would upgrade it to `[MEASURED]` |
|---|---|---|---|
| `[MODELED]` | ECMP-aware ingress of **11.2 Tb/s** (−12.5 %) for leaf-r0 with one spine-1 link down (Section 7.9, Table 7.8) | A closed-form formula: 4 spines × min bundle × 400 Gb/s, assuming uniform demand and unweighted ECMP | On a dedicated lab fabric, drive an all-to-rail-0 load from every other leaf with enough flows, fail one link, and measure per-uplink and aggregate delivered throughput over ≥ 5 runs with a manifest |
| `[SIMULATED]` | Most-loaded-link distribution for 8 flows on 8 links: **2 flows 49.9 %, 3 flows 40.9 %, ≥ 4 flows 8.9 %** (200,000 trials, seed 1; Section 7.6) | A Monte Carlo of uniform random hashing; no real hash function, no congestion control | Count per-link flows on a lab fabric using the NIC's real source-port selection and the switch's real hash (per-port byte counters across many QP setups) |
| `[ILLUSTRATIVE]` | BFD detection **≈ 0.9 s** and sub-second convergence (Table 7.7), or the Section 7.12 checkpoint baseline of **≈ 55 s** | Typical configured values and a teaching scenario, not a run | Timed failover tests (fail a link, timestamp BFD-down, route withdrawal and traffic recovery) repeated ≥ 5 times; or checkpoint timings logged from the real job with a manifest |

A full answer cites the specific number, says why it carries that label (formula, randomized model,
or example), and names a measurement with enough rigour (repetitions, manifest, dedicated fabric) to
justify `[MEASURED]`.
