# Chapter Package Template

Every chapter is a self-contained *chapter package* in `book/part-N-*/chNN-slug/`.

## 1. Folder layout

```text
chNN-slug/
├── README.md              # Chapter card: objectives, prerequisites, time budget, file map, tier
├── manuscript.md          # The chapter text (target 7,000–10,000 words)
├── exercises.md           # Standard exercise set (Section 4 below)
├── lab/
│   ├── README.md          # Lab guide: goal, tier, setup, steps, expected output, deliverable, rubric
│   ├── manifest.yaml      # Environment manifest (tier, python, deps, hardware assumptions, seeds)
│   ├── data/              # Synthetic or captured datasets (committed; small: < 2 MB total)
│   ├── tools/             # Generators for the datasets (deterministic, seeded)
│   ├── starter/           # Learner code with TODOs (must import and run, failing checks gracefully)
│   └── check.py           # Automated checker: `python check.py [--impl starter|solution]`
├── solutions/             # INSTRUCTOR ONLY — answer key
│   ├── exercises-key.md   # Answers, worked solutions, marking guidance for every exercise
│   └── lab/               # Reference implementation that passes check.py
└── review/
    └── REVIEW.md          # Editorial review log: scores per dimension, findings, iteration history
```

`check.py` contract:

- `python lab/check.py --impl solution` must exit 0 (reference passes every check).
- `python lab/check.py --impl starter` must run without crashing and exit non-zero, reporting which
  TODOs remain (learners use this as their progress meter).
- Prints one line per check: `PASS`/`FAIL` + name + short reason. No hardware, no network, no root.
  Must finish in < 60 s on a laptop.

## 2. `manuscript.md` required structure

```markdown
# Chapter NN — Title

> One-paragraph chapter abstract: the engineering problem this chapter solves and why it matters.

## Learning objectives
(5–8 measurable objectives, Bloom verbs: explain, calculate, diagnose, design, validate…)

## Prerequisites and connections
(Which earlier chapters are assumed; which later chapters and capstones build on this one.)

## NN.1 … NN.k  Concept sections
(Architecture and concepts. Each section: mechanism → numbers → evidence → pitfalls.
 Include required data-path diagrams for this chapter.)

## NN.x  Worked example
(A fully worked, end-to-end problem on the ORION reference cluster with all arithmetic shown.)

## NN.y  Hands-on lab overview
(What the lab does, its tier, and what it teaches; link to lab/README.md.)

## NN.z  Troubleshooting scenario
(A realistic incident told through evidence: symptom → evidence → hypotheses ranked → discriminating
 tests → root cause → fix → validation. Must use the diagnostic loop explicitly.)

## Trade-offs and design decisions
(A table of options × criteria, and guidance on when each choice wins.)

## Production operations notes / runbook excerpt
(What an on-call or operator needs: signals, thresholds, safe actions, escalation.)

## Realism boundaries
(What the chapter's labs and models can and cannot demonstrate.)

## Summary
(8–12 bullet key takeaways.)

## Review questions
(Pointer to exercises.md plus 3 quick self-check questions inline.)

## Further reading
(Primary sources with a one-line reason each.)
```

## 3. `README.md` chapter card

Title, one-paragraph summary, learning objectives (copied), prerequisites, estimated time
(read / exercises / lab), lab tier(s), deliverable (from the course outline), file map, and the
14-week course week this chapter belongs to.

## 4. `exercises.md` standard exercise set

| Exercise type | Purpose | Quantity |
|---|---|---|
| Knowledge check | Vocabulary, concepts, protocol/system understanding | 5–8 questions |
| Worked problem | Calculations, architecture reasoning, performance models | 2 problems |
| Hands-on lab | Tools, scripts, configs, traces, datasets (links to `lab/`) | 1 core lab |
| Troubleshooting case | Diagnose a realistic failure from incomplete evidence | 1 scenario |
| Design challenge | Make and defend an engineering trade-off | 1 prompt |
| Reflection / review | Limitations, assumptions, missing evidence | 3–5 questions |

Also include **every chapter exercise listed for this chapter in the course outline** (they are
mandatory) and the chapter **deliverable**. Tag each exercise with difficulty (★ foundational,
★★ intermediate, ★★★ advanced) and the tier required (L1/L2/L3). Each exercise has a stated
"evidence required" line so that grading is objective.

## 5. `lab/README.md` structure

1. Goal and the real-world task it mirrors
2. Tier (L1 laptop/simulation, L2 single-GPU/cloud GPU, L3 multi-node GPU + RDMA/IB) and realism boundary
3. Setup (exact commands; Python version; deps)
4. Background you need (links to manuscript sections)
5. Tasks (numbered; each with expected output or acceptance criterion)
6. Running the checker
7. Deliverable and grading rubric (points per task, totalling 100)
8. Extensions: L2/L3 hardware-backed variant with the exact commands to run on real hardware and what
   to record in the environment manifest
9. Intentionally flawed inputs: describe (for instructors in the solutions folder) which anomalies were
   planted in the dataset and why

## 6. `review/REVIEW.md`

```markdown
# Editorial Review — Chapter NN
| Iteration | Date | Reviewer | Weighted score | Gate |
## Scores by dimension (latest)
## Findings (ID, severity: blocker/major/minor, location, finding, resolution)
## Release-gate items outstanding (external expert review, hardware validation, etc.)
```
