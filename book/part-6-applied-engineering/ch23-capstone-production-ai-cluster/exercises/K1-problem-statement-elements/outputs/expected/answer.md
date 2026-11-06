# K1 — Five elements of a capstone problem statement

**Source:** manuscript Section 23.2 ("The problem statement"); key K1.

A strong problem statement fits in one paragraph and contains five elements. Each one is valuable
because it generates something a reviewer can *recompute or check*, not because it is "documentation".

| # | Element | ORION example | Consequence a reviewer can check |
|---|---|---|---|
| 1 | **Workload** — what runs, at what scale | W-TRAIN: 70 B dense model, 256 GPUs, TP = 8, PP = 4, DP = 8 | FLOPs per step (6·N·tokens), memory per GPU (16 B/param ÷ 32 = 35 GB) and DP/PP traffic can be re-derived |
| 2 | **Numeric objective** | 2 × 10¹² tokens in 120 calendar days, goodput ≥ 0.90 over 30 days | Required tokens/s, and the margin between the 96-day ideal and the 120-day budget, can be checked against the MFU assumption |
| 3 | **Constraints** | Existing 8-rack row, 50 kW per rack (45 kW planned after the 10 % transient margin), budget, schedule | Rack-power invariant (nodes per rack × 10.2 kW max ≤ 45 kW) and rack count can be checked (Table 23.5, invariant 11) |
| 4 | **Scope boundary** | Frontend network and object store are existing services, out of scope | Reviewers know which subsystems they need not review and which *interfaces* (e.g. checkpoint write bandwidth from the PFS) must still be specified |
| 5 | **Evidence tier** | L1 models plus one 2-node L3 measurement | Which numbers may legitimately carry `[MEASURED]`; any 32-node fabric number labelled measured is then a defect (the linter's EVID-004) |

**Why the numbers matter.** "Design a GPU cluster for LLM training" fails every check above: there is
no number to recompute and no constraint to violate. The strong version lets a reviewer, in minutes,
derive throughput from tokens and days, bound nodes per rack from 45 kW, and know what may be measured.

**Common wrong answers.**
- Listing "requirements" or "goals" without a number (no credit: an objective must be falsifiable).
- Confusing scope boundary with constraints: a constraint limits the design; a scope boundary says
  what is *not being designed* but whose interface still matters.
- Omitting the evidence tier, which is the element that most often decides the measurement score.
