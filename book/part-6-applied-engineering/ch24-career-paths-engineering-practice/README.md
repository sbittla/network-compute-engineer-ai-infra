# Chapter 24 — Career Paths and Engineering Practice

**Part VI — Applied Engineering · Course week 14 · Lab tier: L1 (L2/L3 extensions)**

This chapter turns the book's cross-layer knowledge into a career you can prove. It maps six
AI-infrastructure role families (AI network, GPU/HPC, cluster/platform, performance, SRE/operations,
network hardware/vendor) to weighted competency matrices on an evidence-capped 0–4 scale; defines
junior-to-principal levels by observable behaviour; reads the employer landscape as representative
groups rather than claims of current openings, and shows why any job-market claim needs a dated,
deduplicated register; works two complete system-design interviews on the ORION reference cluster (a
W-TRAIN training cluster and a 1,024-GPU RoCEv2 fabric) with all arithmetic; and covers case-study
writing, portfolio building from Capstones A–H, design docs, reviews, on-call hygiene and safety.

## Learning objectives

1. **Map** your current skills to the competency matrix of a target AI-infrastructure role and
   **identify** the three highest-priority gaps with a dated plan to close them.
2. **Distinguish** junior, mid, senior, staff and principal performance by observable behaviours in
   scope, ambiguity, technical judgement, operational ownership and influence.
3. **Evaluate** claims about the job market by demanding a dated, deduplicated register, and
   **validate** such a register programmatically.
4. **Conduct** a 45-minute system-design interview for an AI training cluster or AI network: clarify
   requirements, derive capacity numbers, draw data paths, analyse failure domains and defend
   trade-offs.
5. **Write** an incident or performance case study that separates measured facts, inferred causes and
   remaining uncertainty, and states impact in units a reader can check.
6. **Assemble** a portfolio from the book's capstones in which every claim is labelled measured,
   modeled, simulated or illustrative.
7. **Apply** professional engineering practice — design documents, design reviews, on-call hygiene and
   change safety — to your own work.

## Prerequisites

The whole book, especially Chapters 1, 2, 7, 8, 11, 12, 14, 18, 20, 21, 22 and 23. At least one
capstone ([capstones/](../../../capstones/)) completed or in progress.

## Time budget

| Activity | Estimate |
|---|---|
| Reading | 3.5 h |
| Exercises (incl. M2 presentation rehearsal) | 6–8 h |
| Lab (L1) | 2–3 h, plus 1 h scoring your own evidence |

## Deliverable (course outline)

Role-readiness matrix, portfolio narrative, and technical presentation.

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text |
| [exercises.md](exercises.md) | Knowledge checks, worked problems, lab, troubleshooting case, design challenge, outline-mandated exercises (M1–M3), reflection |
| [lab/README.md](lab/README.md) | Lab guide: role-readiness scorer and job-posting register validator |
| `lab/manifest.yaml` | Environment manifest (L1, seed 24) |
| `lab/data/` | Competency matrices, sample learner evidence, **synthetic** job register (fictional employers, `example.com` URLs) |
| `lab/tools/generate_data.py` | Deterministic data generator — instructor copy only, removed from the student release |
| `lab/starter/career_lab.py` | Learner module with TODOs |
| `lab/check.py` | Checker: `python check.py [--impl starter|solution]` |
| `solutions/` | Instructor answer key and reference implementation (remove before distributing) |
| [review/REVIEW.md](review/REVIEW.md) | Editorial review log |
