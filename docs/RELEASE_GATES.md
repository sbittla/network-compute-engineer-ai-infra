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
| G1 | Validate every lab on its stated tier; publish exact prerequisites, versions, expected outputs, limitations | L1: **done** — every package runs in its own Docker image (`docker/lab.Dockerfile`, pinned runtime, `--network none`); `python scripts/docker_labs.py ci` builds all 64 images, then runs 2,144 tests: 32/32 packages pass, including 480 exercise folders whose 170 `solve.py` solvers regenerate their committed outputs exactly. CI runs the same on every push (`.github/workflows/labs.yml`). `scripts/validate_labs.py` also 32/32. L2/L3 extensions: **not yet run on hardware** | Lab engineer with GPU/RDMA access |
| G2 | Experienced GPU-cluster/network engineer reviews topology, RDMA, NCCL, checkpointing, failure-recovery chapters (5, 8, 9, 12, 13, 14, 19) | Open | External technical reviewer |
| G3 | Data-centre facilities specialist reviews power, liquid cooling, CDU, PDU, MEP material (2, 21) | Open | External facilities reviewer |
| G4 | Verify every `[VENDOR-SPEC]` claim and version-sensitive API against current primary documentation; record date and platform | **First pass done (2026-10-30):** 282 claims checked against primary sources (vendor docs, tagged source, standards): 244 OK, 12 WRONG fixed, 22 version qualifiers added, 4 unverifiable (already hedged). Per-group evidence in [verification/](verification/); shared facts in VERIFIED_FACTS.md. Re-run before each printing — DCGM, NCCL, Kueue and vLLM changed names during 2026 | Technical editor |
| G5 | Run all benchmark and failure-injection procedures in a safe lab; preserve raw results | Open (L1 simulations done) | Lab engineer |
| G6 | Technical copyedit for terms, diagrams, units, acronyms, and measured-vs-illustrative separation | **Book-wide machine-assisted copyedit done (2026-10-30):** register in COPYEDIT_REGISTER.md (955 findings; ≈ 577 mechanical and ≈ 415 judgement edits applied, rest recorded as false positives). `scripts/copyedit_lint.py` → 0 findings in 113 files; 0 broken links or cross-references; units verified. Evidence in [verification/](verification/). **A human copyeditor's read-through is still recommended before print** | Copyeditor |
| G7 | Refresh job-market mapping (Chapter 24) with a dated, deduplicated register | **Done (2026-10-30):** 42 deduplicated roles from 11 employers' own listings (`lab/data/job_register_2026-10.csv`, report in [verification/G7-ch24.md](verification/G7-ch24.md)). Gaps: no hyperscalers, mostly US. Stale after 2026-11-29 — refresh before publication | Author |
