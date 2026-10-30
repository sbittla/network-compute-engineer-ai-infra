# Chapter 22 — Exercises: Cross-Layer Performance Engineering

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/simulation ·
L2 single GPU host · L3 multi-node GPU + RDMA. Every exercise states the evidence required for grading.
Numbers given in prompts are `[ILLUSTRATIVE]` unless labelled otherwise.

**Chapter deliverable (course outline):** an *evidence-based root-cause report and validated
optimization* — the before/after report from the lab (Exercise O3) plus a validation plan, with MDE,
for the optimization you recommend (Exercise O3-c); L3 learners execute the validation.

---

## Knowledge checks

**K1 ★ (L1).** Write the step-time equation used in this chapter. For the terms
`T_comm,exposed` and `T_data,exposed`, name one evidence source on ORION that measures each directly.
*Evidence required:* the equation with all six terms; one named tool or metric per term with its grain.

**K2 ★ (L1).** A dashboard shows 98 % "GPU utilisation" on every GPU of a job whose step time rose 15 %.
Explain why this does not show the GPUs are busy computing, and name two better signals.
*Evidence required:* definition of the utilisation metric; two named alternatives and what each measures.

**K3 ★ (L1).** Mean step time of a workload family rose 20 %; the median of per-job means rose 4 %; per-job
p99 is unchanged for most jobs. What kind of cause does this pattern suggest, and which partition of the
jobs would you try first?
*Evidence required:* an interpretation of mean vs median; one concrete partition and the hypothesis it tests.

**K4 ★★ (L1).** Define a *discriminating test*. Give one example from the W-TRAIN sweep that
discriminates H-placement from H-network, and one non-example.
*Evidence required:* definition; the example with each hypothesis's predicted outcome; why the non-example fails.

**K5 ★★ (L1).** Why does the attribution model include a period indicator (`after`) in addition to the
change-specific factors? What would go wrong without it?
*Evidence required:* the role of the term; a concrete misattribution it prevents.

**K6 ★ (L1).** Define weak- and strong-scaling efficiency. Which applies when W-TRAIN goes from the
64-GPU ablation (DP = 2) to the 256-GPU run (DP = 8), and why?
*Evidence required:* both formulas; the choice with the reason (what is held constant).

**K7 ★★ (L1).** Explain survivorship bias in a training-regression analysis and why it particularly
affects placement-related regressions.
*Evidence required:* definition in this context; the mechanism linking slow jobs to failed jobs.

**K8 ★★ (L1).** Give two reasons why rolling back a change in production "to see if it helps" is a poor
diagnostic, even when the rollback is safe.
*Evidence required:* two distinct reasons (confounding/time variation; information value vs cost/risk).

---

## Worked problems

**W1 ★★ (L1) — Attribution with an interaction.** Before a change window, 10 W-TRAIN ablation jobs had a
job-weighted mean step time of 17.40 s. After the window, 10 jobs ran with the exposures below
(P = TP group split across nodes, S = dataset on capacity tier):

| Cell | Jobs | Mean step (s) |
|---|---|---|
| P = 0, S = 0 | 4 | 17.6 |
| P = 1, S = 0 | 3 | 24.8 |
| P = 0, S = 1 | 2 | 19.4 |
| P = 1, S = 1 | 1 | 28.2 |

a. Compute the after-period mean, the delta in seconds, and the percentage regression.
b. Using cell means, compute the period shift, the effect of P (at S = 0), the effect of S (at P = 0),
   and the P × S interaction.
c. Attribute the delta to period shift, P, S, and the interaction (contribution in s and share in %).
   Show that the contributions sum to the delta.
d. Compute the naive within-after differences "mean(P=1) − mean(P=0)" and "mean(S=1) − mean(S=0)".
   Why do they differ from (b)?
e. The interaction is positive. Propose a mechanism that would make S hurt more when P = 1.

*Evidence required:* all arithmetic; a balanced attribution table; one-paragraph mechanism.

**W2 ★★ (L1) — Scaling efficiency and detectability.** W-TRAIN ablations measure median step times of
17.38 s (64 GPUs, DP = 2), 17.62 s (128 GPUs, DP = 4), and 17.90 s (256 GPUs, DP = 8); per-GPU work is
constant.

a. Compute tokens/s and weak-scaling efficiency at 128 and 256 GPUs relative to 64 GPUs.
b. Using the straggler model of Section 22.5.2 with per-node jitter σ = 0.5 s and expected maxima of
   1.42σ (8 nodes), 1.77σ (16 nodes), and 2.07σ (32 nodes), how much of each gap does straggling
   explain? What remains?
c. A vendor proposes an NCCL setting that "saves 0.15 s per step" at 256 GPUs. Run-to-run σ of per-job
   means is 0.11 s. Can 5 runs per arm detect it (MDE at 5 % two-sided, 80 % power)? How many runs per arm
   would you need?

*Evidence required:* formulas, substituted values, results with units; a clear yes/no with n.

---

## Hands-on lab

**L1 ★★ (L1) — Attribute a cross-layer regression.** Complete [the Chapter 22 lab](lab/README.md):
tasks 1–9 in `starter/regression_lab.py`, until `python lab/check.py` reports 10/10 PASS.
*Evidence required:* checker output; generated `report.md`; a short note listing each data-hygiene rule
and how many rows or jobs it affected.

---

## Troubleshooting case

**T1 ★★★ (L1 analysis; L3 to confirm) — Periodic stalls on the full run.** The 256-GPU W-TRAIN run's
median step time moved from 17.9 s to 18.5 s, and roughly every 30–50 steps one step takes 24–27 s. All
ranks see the long steps at the same step numbers. Evidence collected so far:

```text
data_wait per step:            0.04–0.06 s on all ranks, including the long steps
per-rank collective wait:      unimodal; on long steps every rank waits 6–9 s
DCGM:                          clocks 1,830 MHz, no slowdown reasons, temperatures 65–70 °C
NCCL (2.23+):                  no timeouts; NET channel lines end in /GDRDMA on all nodes
orion-be-leaf-r3 Ethernet28 (→ orion-n15 NIC3), 10-minute deltas:
    FEC corrected codewords   1.9e9   (other ports: 1–4e6)
    FEC uncorrectable         312     (other ports: 0)
    in-errors (CRC)           297
orion-n15: ethtool -S <rail-3 netdev> | grep -E 'rx_crc_errors_phy|rx_symbol_err_phy'
    rx_crc_errors_phy: 4,118   (rising)      rx_symbol_err_phy: 89,233 (rising)
orion-n15: /sys/class/infiniband/mlx5_3/ports/1/hw_counters/out_of_sequence  rising; local_ack_timeout_err rising
change log: none for ORION in 72 h; orion-n15 had a NIC3 optic reseated 3 days ago
```

a. Build a hypothesis tree with at least four leaves and state each leaf's predicted fingerprint.
b. Rank three next tests by information value, cost, and risk.
c. State the most likely root cause and the full causal chain from physical layer to step time.
d. Specify the safe fix (who, what scope, what acceptance test) and the validation with numbers.

*Evidence required:* tree; ranked test table with scores; causal chain naming the counters that support
each link; a fix plan that obeys the runbook's "not without change approval" list; validation criteria.

---

## Design challenge

**D1 ★★★ (L1) — Continuous regression detection for ORION.** Design a system that detects a ≥ 3 %
training-throughput regression within one day of a change window and produces a first attribution
automatically. Consider: dedicated canary benchmark jobs versus mining production jobs (natural
experiments), the GPU cost of reserved canaries on a 32-node cluster, the change-calendar and inventory
joins (time-aware), statistical thresholds (σ, MDE), and false-positive cost.
*Evidence required:* architecture sketch; a trade-off table with at least two options and four criteria
(detection time, GPU cost, false-positive rate, causal strength); a stated recommendation with the
arithmetic for canary cost and detectable effect.

---

## Reflection / review

**R1 ★ (L1).** Your lab attribution leaves 8.3 % of the regression as a common shift (period indicator) not attributable to a named change. List three
explanations consistent with the evidence, and the test that would separate them.

**R2 ★★ (L1).** The lab's model fitted with R² ≈ 0.998. Why is a high R² *not* evidence that the
factors are causes?

**R3 ★★ (L1).** Which conclusions in your lab report would change if the population excluded failed jobs?
Which would not?

**R4 ★ (L1).** What can the L1 lab not tell you about the GPUDirect RDMA hypothesis, and exactly what
L2/L3 evidence would close the gap?

*Evidence required (R1–R4):* concise written answers, each naming the evidence (or missing evidence) it
relies on.

---

## Outline-mandated exercises (course outline Section 14, Chapter 22)

**O1 ★★ (L1) — Investigate an end-to-end workload regression using supplied GPU, CPU, network,
storage, and scheduler metrics.** Using the lab bundle:
a. Complete lab tasks 1–7.
b. For each inferred cause, cite one *direct* measurement from `node_metrics.csv`, `node_inventory.csv`,
   or `nccl_init_sample.log` (GPU, CPU, network, or storage layer) that corroborates it, with numbers.
c. Fit the model again with a `tp_split × driver_new` and a `tp_split × storage_new` interaction term.
   Report the coefficients and state whether the additive attribution is defensible.
*Evidence required:* checker output; a corroboration table (cause × direct evidence × values);
interaction coefficients with a one-sentence judgement.

**O2 ★★ (L1) — Build a hypothesis tree and rank tests by information value, cost, and risk.**
a. Draw the hypothesis tree for the lab regression (Mermaid or drawn), rooted in the step-time equation,
   with every change, alert, and anomaly attached to a term and a predicted fingerprint.
b. Complete lab task 8 and add two tests of your own with justified information value, cost, risk, and
   environment; place them in the ranking.
*Evidence required:* tree; ranked table including your two tests with scores; the list of rejected
tests and the rule applied.

**O3 ★★★ (L1; L3 optional) — Write a before/after report that separates measured facts, inferred causes,
and remaining uncertainty.**
a. Complete lab task 9, then edit the generated report into a one-page document for the four change
   owners, following Section 22.9.
b. Include the data-hygiene rules applied and their effects, and the verdict on the `orion-n13` alert with
   its evidence.
c. Add a "Recommended changes and validation" section: for each fix, the predicted effect (range), the
   canary scope, the MDE for your proposed n, and an abort condition. L3 learners execute the
   placement A/B from the lab README and add the results labelled `[MEASURED]` with a manifest.
*Evidence required:* the report; every number labelled; no causal language in "Measured facts".
