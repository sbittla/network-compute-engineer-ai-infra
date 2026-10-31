# D1 — A 12-week plan from "near" to "ready": reference answer and marking notes

There is no single answer: each learner plans from their own lab report. The reference below uses the lab's
sample learner at **AI Network Engineer / senior** (Table 24.5) so markers can check arithmetic. All scores
are `[MODELED]` from rule-adjusted evidence; hours are `[ILLUSTRATIVE]`.

**Current matrix.** Score 13.333 / 17 = **78.4 %, near** (max gap 2 on observability). Gap plan: observability
(priority 4), congestion (3), host_topology (2), physical_layer (2) (Section 24.2).

**Plan (≤ 10 h/week, 120 h budget), depth-first.**

| Weeks | Artifact | Hours | Raises | Projected score / status |
|---|---|---|---|---|
| 1–7 | Capstone B (telemetry and troubleshooting), with ADRs and a case study in Table 24.12 form | 65 | observability 1 → 3, congestion 2 → 3 | (13.333 + 1.333 + 1.000) / 17 = 15.667 / 17 = **92.2 %, ready** (max gap 1) |
| 8–10 | L2 GPU-host lab: GPU↔NIC topology and `ib_write_bw --use_cuda` per rail, with manifest | 25 (+ rented GPU time) | host_topology 2 → 3 (+0.667) | 16.333 / 17 = 96.1 %, ready |
| 11–12 | Portfolio narrative (≤ 1 page), peer review of the capstone, rehearsal of M2 | 20 | none (verifies existing levels) | unchanged |

Checks: observability term 2 × 3/3 = 2.000 instead of 0.667 (+1.333); congestion 3 × 3/3 = 3.000 instead of
2.000 (+1.000). Remaining gaps after Capstone B: physical layer 1, host topology 1 → max gap 1, so the
gap-blocks-ready rule no longer applies.

**Why depth over breadth.** Two L1 capstones would not be L1 *labs*, but a breadth plan of L1 labs caps every
competency at 2, which cannot close a target-3 gap (Figure 24.5). One capstone that hits the two
highest-priority gaps at once (Table 24.13: Capstone B raises congestion, RDMA, observability and physical
layer) moves the score most per hour. Paying for L2 time is justified only for host_topology, where a
hardware-backed measurement is the evidence an interviewer will probe.

**Not doing.** No level-4 claims (they need production ownership with a verifier); no certification
(capped at 1); no new competencies outside the matrix; no L3 multi-node work (cost and access exceed the
budget, and the score is already ready without it).

**Deductions.** Plans whose artifacts cannot reach the claimed level (an L1 lab "raising" a competency to 3);
hours over budget; no projected score after each artifact.
