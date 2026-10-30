# Chapter 24 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/analysis · L2 single
GPU host · L3 multi-node GPU + RDMA. Every exercise states the evidence required for grading. Use the
ORION values in [docs/REFERENCE_CLUSTER.md](../../../docs/REFERENCE_CLUSTER.md) unless an exercise says
otherwise, and label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.

## A. Knowledge checks

**K1 ★ L1 — Roles by what they are paged for.** For the six role families in Table 24.1, name one
incident each is typically paged for (or, for the performance engineer, the investigation it owns)
and the first piece of evidence that role would collect.
*Evidence required:* six rows: role, incident, first evidence (command, counter or log).

**K2 ★ L1 — Evidence caps.** Explain why a completed course cannot demonstrate more than level 1 and a
Level-1 lab not more than level 2 on the chapter's proficiency scale. What must a piece of evidence add
to support level 3? Level 4?
*Evidence required:* one paragraph per level boundary, each naming the observable behaviour that changes.

**K3 ★ L1 — Senior versus staff.** Using Table 24.6, describe how a senior and a staff engineer would
each respond to the third optics-related bandwidth degradation in a quarter. Which *outcomes* would
appear in each one's promotion packet?
*Evidence required:* two short paragraphs; at least two outcomes per level, phrased as verifiable results.

**K4 ★ L1 — The register.** List the fields the course outline requires in a job-posting register and,
for any three, the specific error in a market claim that the field prevents.
*Evidence required:* complete field list; three field → failure-mode pairs.

**K5 ★★ L1 — TP inside the node.** State the calculation from Section 24.6 that shows TP = 8 must stay
inside the NVLink domain for W-TRAIN. Give the per-step TP volume per GPU and the time it would take
over NVLink and over a NIC under the chapter's assumptions.
*Evidence required:* formula, substituted values, both times with units and labels.

**K6 ★★ L1 — Where the bytes go.** Explain why rail-aligned W-TRAIN traffic on ORION-256 never crosses a
spine, and why that stops being true in the 1,024-GPU fabric of Section 24.7.
*Evidence required:* the placement/rail argument for each case; the number of leaves per rail in each.

**K7 ★ L1 — Discriminating tests.** Define a discriminating test. In the troubleshooting round of
Section 24.12, which single test separates "physical-layer degradation" from "congestion", and what
result would have pointed the other way?
*Evidence required:* definition; the test; both possible outcomes and what each implies.

**K8 ★ L1 — Representative, not current.** Why does the chapter insist that employers in Table 24.7 are
"representative, not a claim of current openings"? Give one way a reader could be misled if that
qualification were dropped.
*Evidence required:* two to four sentences.

## B. Worked problems

**WP1 ★★ L1 — Readiness for a second role.** Using the sample learner's demonstrated levels (Section
24.2: observability 1, reliability/security 2, automation 3, scheduling 1, storage/checkpointing 1,
Linux host 2, communication 3) and the AI Infrastructure SRE / Operations matrix in
`lab/data/competency_matrices.yaml` at **mid** level:
(a) compute the readiness score with every term shown; (b) give the status and why; (c) produce the gap
plan ordered by priority; (d) compute the new score and status if Capstone F raises observability to 3.
*Evidence required:* a table of w, d, t and w·min(d,t)/t; the score to one decimal; ordered gap list with
priorities; the recomputed score and status.

**WP2 ★★★ L1 — A 512-GPU variant.** Halcyon AI considers a 512-GPU (64 × HX8) cluster with the same
64-port 400G switches, rail-optimised and non-blocking.
(a) Size it: leaves per rail, total leaves, spines, links per leaf–spine pair, total links.
(b) If 32 equal RoCE flows leave a leaf on 32 uplinks with random ECMP hashing, how many uplinks are
idle on average? Recompute with 4 queue pairs per connection (128 flows of one quarter the size each).
(c) For W-TRAIN on ORION-256, recompute Young's checkpoint interval and the total overhead if the
node MTBF halves from the canonical 1,536 h to 768 h (C = 12.25 s, restart 900 s).
*Evidence required:* every formula with substituted values and units; results labelled `[MODELED]`.

## C. Hands-on lab

**L1 ★★ L1 — Role-readiness scorer and register validator.** Complete
[lab/README.md](lab/README.md) Tasks 1–8, produce `readiness_report.md`, and explain every evidence
flag raised for the sample learner.
*Evidence required:* `python check.py` output showing 11/11 PASS; the generated report; a one-page
explanation of the flags (rule, why it exists, what the learner should do).

## D. Troubleshooting case

**T1 ★★★ L1 — The interview troubleshooting round, version 2.** An interviewer gives you this
`[ILLUSTRATIVE]` evidence: a 32-node W-TRAIN job on ORION-256 is 12 % slower than yesterday
(step-time p50 17.4 s → 19.5 s). Per-rank timing shows ranks on `orion-n22` are last to arrive at every
pipeline send. On `orion-n22`, `nvidia-smi -q -d PERFORMANCE` shows for GPU 5 (abridged):

```text
    Clocks Event Reasons
        Idle                              : Not Active
        SW Power Cap                      : Not Active
        HW Slowdown                       : Not Active
            HW Thermal Slowdown           : Not Active
            HW Power Brake Slowdown       : Not Active
        SW Thermal Slowdown               : Active
```

Its SM clock is 1,715 MHz against 1,980 MHz on peers (peers run application clocks locked at the
≈ 1,980 MHz maximum boost, not ORION's typical ≈ 1,830 MHz sustained clock); GPU temperature is 89 °C against 64–70 °C on
peers. The fabric dashboard also shows ECN-marked packets on rail-5 leaf ports rising 3× since
yesterday, and the facilities log records a fan-tray replacement in `rack-06` (which holds `orion-n22`) at
02:10. Walk the diagnostic loop: rank at least three hypotheses by information value, cost and risk;
name the discriminating test(s); state the root cause and what remains correlation; propose a safe
change and a validation; check that the clock deficit explains the size of the slowdown; and propose
an explanation for the ECN signal and how you would test it.
*Evidence required:* hypothesis table; discriminating test with expected outcomes; root-cause statement
separated into proven and inferred; magnitude check with arithmetic; safe action; validation with
repetitions; ECN hypothesis with its test.

## E. Design challenge

**D1 ★★★ L1 — A 12-week plan from "near" to "ready".** Pick a role and level at which your own
readiness (from the lab) is "near" or "not_ready". Design a 12-week plan to reach "ready" with no more
than 10 hours per week. Choose between depth (one capstone to level 3 plus a hardware lab) and breadth
(two capstones at L1), and between L1-only and paying for L2 GPU time. Defend the choice with the
readiness arithmetic and the evidence caps.
*Evidence required:* current matrix; plan with dated artifacts and hours; projected score and status
after each artifact; one paragraph on what you are *not* doing and why.

## F. Outline-mandated exercises and deliverable

**M1 ★★ L1 — Target role and skills map** *(course outline, Chapter 24 exercise 1)*. Select a target
role and map your current skills to its competency requirements using the lab's matrices (or your
employer's ladder, mapped onto the 0–4 scale). Every demonstrated level must cite an artifact.
*Evidence required:* the lab report run on your evidence file; a matrix with role, two adjacent roles,
four seniority columns; top three gaps with dated actions.

**M2 ★★★ L1 — System-design interview presentation** *(course outline, Chapter 24 exercise 2)*.
Prepare a 20-minute presentation (10–14 slides or a whiteboard script) for an AI-cluster or AI-network
design problem — either walk-through in Sections 24.6–24.7 with one changed constraint you choose, or a
new prompt. Rehearse it aloud with a timer and record the time.
*Evidence required:* assumptions table with labels; all capacity arithmetic; at least one data-path
diagram; failure-domain table; day-one validation plan; answers to two follow-ups you anticipate;
rehearsal time.

**M3 ★★ L1 — Case study** *(course outline, Chapter 24 exercise 3)*. Write a concise (≤ 800 words)
incident or performance case study using Table 24.12's structure. Use a real case anonymised onto
ORION, or a capstone result.
*Evidence required:* every Table 24.12 section present; impact in units with arithmetic; at least one
discriminating test; a "remaining uncertainty" paragraph; a statement of what was anonymised.

**Deliverable** *(course outline)*: **role-readiness matrix** (M1), **portfolio narrative** (≤ 1 page,
Section 24.9), and **technical presentation** (M2).

## G. Reflection and review

**R1 ★ L1.** The readiness score is MODELED from self-reported evidence. Name two ways it could be
systematically wrong for you, and what external evidence would correct each.

**R2 ★ L1.** Which competency in your target role's matrix do you think is mis-weighted for the employers
you are targeting? Argue for a different weight using the problems in Table 24.7.

**R3 ★★ L1.** Your Level-1 labs produced many numbers. Which of them could you defend in an interview as
evidence of skill, and which only as evidence of reasoning? Where is the line?

**R4 ★★ L1.** The synthetic register suggests "python" is the most common required skill. What would you
need — beyond a real, dated register — before concluding that Python skill is a hiring bottleneck for
your target role?

*Evidence required (R1–R4):* 100–200 words each, naming specific evidence rather than general intent.
