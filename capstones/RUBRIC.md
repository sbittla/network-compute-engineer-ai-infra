# Capstone Scoring Rubric

Every capstone (A–H) is scored on the seven dimensions of the course outline's capstone rubric
(Section 17). Each capstone README adds a "what excellent looks like" row per dimension, and each
instructor grading guide gives capstone-specific evidence. This file is the common standard.

## 1. Dimensions, weights and thresholds

| # | Dimension | Weight | 9–10 / excellent evidence (course outline) |
|---|---|---|---|
| R1 | Problem framing and assumptions | 10 | Workload, scale, constraints and assumptions are explicit, realistic and testable |
| R2 | Architecture and technical correctness | 20 | Compute, network, storage and orchestration design is coherent; data paths and dependencies are correctly explained |
| R3 | Implementation / reproducibility | 15 | Scripts, configurations, models or simulations are repeatable; environment and limitations are documented |
| R4 | Measurement and analysis | 20 | Baselines, percentiles, scaling, utilization and comparisons use sound methods; conclusions match evidence |
| R5 | Reliability, security and operations | 15 | Failure domains, isolation, SLOs, rollback, recovery and operational ownership are addressed |
| R6 | Troubleshooting and engineering judgment | 10 | Hypotheses are ranked, tests are discriminating, root cause is evidence-based and trade-offs are acknowledged |
| R7 | Communication and portfolio quality | 10 | Diagrams, report, runbooks and presentation are clear enough for another engineer to review and reproduce |

- **Pass:** total ≥ **70/100**, *and* at least **50 %** of the weight in **R2** (≥ 10/20) and in **R4** (≥ 10/20).
- **Distinction:** total ≥ **90/100** *with reproducible evidence*: every quantitative claim regenerates
  from committed code and inputs, and any `[MEASURED]` claim has an environment manifest and repetitions.
- **Automatic cap:** presenting `[SIMULATED]`, `[MODELED]` or laptop-proxy numbers as physical
  measurements caps R4 at 40 % (8/20). Because 8 < 10, the R4 minimum (50 % of 20), that alone fails the
  capstone, by design.

## 2. Level descriptors

Score each dimension as a fraction of its weight. Pick the level whose description fits, then place the
score within the band.

| Dimension | Exemplary (90–100 %) | Proficient (70–89 %) | Developing (50–69 %) | Insufficient (< 50 %) |
|---|---|---|---|---|
| R1 Framing | Testable success criteria with numbers; assumptions register ranked by sensitivity; top assumptions have validation plans | Criteria and register complete; sensitivity informal | Assumptions listed but not quantified; criteria qualitative | Problem restated from the brief; assumptions implicit |
| R2 Correctness | All arithmetic and mechanisms correct; data paths drawn end to end; every planted trap in the dataset handled and explained | One minor error that does not change a conclusion | An error that changes a secondary conclusion, or a planted trap missed | Core mechanism or arithmetic wrong; design would fail in practice |
| R3 Reproducibility | All starter-kit checks pass; one command regenerates every number; versions pinned; own tests added | All checks pass; reproduction needs some manual steps | Most checks pass; reproduction incomplete | Checks failing or results not reproducible |
| R4 Measurement | Sound method (warm-up, repetitions, percentiles, spread, significance or sensitivity as appropriate); comparisons matched; labels perfect; conclusions no stronger than the evidence | Method sound with gaps (e.g., no sensitivity or no CI) | Single operating point, means without spread, or weak labelling | Unsupported claims, or measured/modeled confusion (cap 40 %) |
| R5 Reliability, security, ops | Failure domains quantified; runbooks with safe first steps, approvals and owners; rollback and recovery tested or simulated; concrete security controls | Most elements present; some owners or controls generic | Generic FMEA or runbook | Absent |
| R6 Judgment | Ranked hypotheses with discriminating tests; proven cause separated from correlation; states what would change the decision | Sound reasoning, fewer alternatives considered | Single hypothesis; trade-offs asserted | Conclusions contradict the evidence |
| R7 Communication | A reviewer grasps the decision in 5 minutes and reproduces a number in 30; captioned figures; consistent units and labels | Clear but long or uneven | Hard to follow; figures unlabelled | Disorganized or incomplete |

## 3. How R5 can be evidenced

Every capstone needs operational evidence with safe first steps, approvals and owners, but the form can
differ. Capstones B, D, E, F, G and H use runbook or rollout templates. Capstone A can meet the runbook
part of R5 through its staged acceptance plan (owners, entry/exit criteria) plus `templates/runbook.md`
(rail-leaf failure, rack power-cap event). Capstone C can meet it through the launcher preflight and
scaling-regression procedures in `templates/runbook.md`. A submission whose only operational content is
a generic FMEA scores Developing on R5.

## 4. Specialization mini-capstone

A mini-capstone is a second capstone at reduced scope: its starter kit, plus three of its artifacts
chosen by the learner. It is graded on **R3, R4 and R6 only**, as a subtotal out of **45** (15 + 20 + 10)
with the same level descriptors.

- **Pass:** ≥ 32/45 (≈ 70 %) **and** R4 ≥ 10/20.
- **Measurement cap:** the R4 cap for measured/modeled confusion applies unchanged (8/20, a fail).
- **Recording:** the mini-capstone is recorded **separately** as a role-specialization credit on the
  learner's record. It does **not** change the capstone's 35 % weight in the course assessment, which is
  computed from the primary capstone alone. A failed mini-capstone has no effect on the course grade.

## 5. Required sections (all capstones)

A submission missing any of these cannot score above Developing in R7. The missing section also
caps the dimension it belongs to at Developing:

problem statement (R1) · architecture (R2) · assumptions (R1) · implementation or simulation boundary
(R3/R4) · test plan (R4) · results (R4) · failure analysis (R5) · security considerations (R5) · final
engineering review (R6/R7).

## 6. Grader worksheet

Copy this table per submission. Record evidence as file and section references, not impressions.

```text
Learner: ____________________   Capstone: __   Tier(s): L1 / L2 / L3   Grader: __________   Date: ________

| Dim | Weight | Level (E/P/D/I) | Score | Evidence (file §) | Key finding |
|-----|--------|-----------------|-------|-------------------|-------------|
| R1  | 10     |                 |       |                   |             |
| R2  | 20     |                 |       |                   |             |
| R3  | 15     |                 |       |                   |             |
| R4  | 20     |                 |       |                   |             |
| R5  | 15     |                 |       |                   |             |
| R6  | 10     |                 |       |                   |             |
| R7  | 10     |                 |       |                   |             |
| Total | 100  |                 |       |                   |             |

Gate checks
[ ] check.py: ___/___ checks pass (run: python check.py in the learner's starter-kit)
[ ] R2 >= 10 and R4 >= 10
[ ] No measured/modeled confusion (else R4 capped at 8)
[ ] All nine required sections present
[ ] Distinction only: every number regenerates; MEASURED claims have manifests and >= 5 repetitions

Result:  Fail  /  Pass  /  Distinction        Total: ____ / 100

Top 3 strengths:
Top 3 required improvements:
Viva questions asked and quality of answers:
```

## 7. Calibration

- Graders score the instructor `EXEMPLAR.md` of each capstone first. It should land at 90–95; if it does
  not, discuss before grading learners.
- Two graders score 10 % of submissions independently. Differences larger than 8 points total, or a
  level apart on R2 or R4, are reconciled in discussion.
- L2/L3 work earns credit inside R3 and R4 through better evidence. There is no bonus outside the 100
  points, and an L1-only submission can earn a distinction.
