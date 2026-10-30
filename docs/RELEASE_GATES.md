# Release Gates

The book uses two levels of gating.

## 1. Internal editorial gate (per package)

Defined in [EDITORIAL_RUBRIC.md](EDITORIAL_RUBRIC.md): weighted ≥ 9.5, no dimension < 9.0, labs
validated, no open blocker/major findings, all outline-mandated exercises present. Each package's
`review/REVIEW.md` records the author self-review and the independent review iterations. The current
status of every package is summarised in [REVIEW_STATUS.md](REVIEW_STATUS.md).

## 2. External publication gates (outstanding)

These come from Section 23 of the course outline. An internal editorial score is not a substitute for
them, and the book should not be described publicly as a "9.5+ definitive edition" until they close.

| # | Gate | Status | Owner |
|---|---|---|---|
| G1 | Validate every lab on its stated tier; publish exact prerequisites, versions, expected outputs, limitations | L1: **done** — 32/32 labs pass `scripts/validate_labs.py` (solution, starter, student-release no-generator, docs lint). L2/L3 extensions: **not yet run on hardware** | Lab engineer with GPU/RDMA access |
| G2 | Experienced GPU-cluster/network engineer reviews topology, RDMA, NCCL, checkpointing, failure-recovery chapters (5, 8, 9, 12, 13, 14, 19) | Open | External technical reviewer |
| G3 | Data-centre facilities specialist reviews power, liquid cooling, CDU, PDU, MEP material (2, 21) | Open | External facilities reviewer |
| G4 | Verify every `[VENDOR-SPEC]` claim and version-sensitive API against current primary documentation; record date and platform | Open — claims are flagged inline as `[VENDOR-SPEC, 2026-10]`; reviewer-verified items recorded in VERIFIED_FACTS.md | Technical editor |
| G5 | Run all benchmark and failure-injection procedures in a safe lab; preserve raw results | Open (L1 simulations done) | Lab engineer |
| G6 | Technical copyedit for terms, diagrams, units, acronyms, and measured-vs-illustrative separation | Internal pass done per package (2–4 independent iterations each); shared terms/numbers centralised in REFERENCE_CLUSTER.md and VERIFIED_FACTS.md; full-book human copyedit open | Copyeditor |
| G7 | Refresh job-market mapping (Chapter 24) with a dated, deduplicated register | Open — Chapter 24 provides the register schema and validator | Author |
