# K4 — Discriminating test: definition and examples (solution)

**Definition (Section 22.3.3).** A test is *discriminating* when the competing hypotheses predict
*different* outcomes for it, so whatever the result, at least one hypothesis loses credibility.

**Example from the W-TRAIN sweep: partition after-period jobs by whether any TP group spans two nodes.**

| Hypothesis | Predicted outcome |
|---|---|
| H-placement (TP all-reduce moved from NVLink to the backend NICs) | A large gap aligned with TP span: split jobs ≈ 9 s per step slower, packed jobs near baseline (lab: TP-split coefficient +8.96 ± 0.10 s `[SIMULATED]`) |
| H-network (fabric congestion) | All multi-node jobs slow similarly, since DP and PP traffic crosses the fabric for every 64-GPU job; no gap aligned with TP span |

The test uses data already held (placement records), costs minutes and carries no risk; in the lab this
is T1 (info 0.9, 0.5 h, low → score 1.8).

**Non-example: "look at the fabric dashboard".** TP-split jobs push TP traffic onto the backend (lab:
backend tx per node 6 → 96 GB/s), GDR-off jobs add host-staged traffic, and genuine congestion raises
ECN and PFC counters. Every hypothesis predicts "something odd" there, so whatever is seen, no
hypothesis is eliminated. Other non-examples: rerunning the same job ("it is still slow" is predicted by
all hypotheses), or rolling back the most recent change (confounded; see K8).

**Common wrong answers.** Defining a discriminating test as "a test that confirms the hypothesis";
giving an example that both hypotheses predict the same way.
