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
| G1 | Validate every lab on its stated tier; publish exact prerequisites, versions, expected outputs, limitations | L1: **done** — every package runs in its own Docker image (`docker/lab.Dockerfile`, pinned runtime, `--network none`); `python scripts/docker_labs.py ci` builds all 64 images, then runs 2,144 tests: 32/32 packages pass, including 480 exercise folders whose 170 `solve.py` solvers regenerate their committed outputs exactly. CI runs the same on every push (`.github/workflows/labs.yml`). `scripts/validate_labs.py` also 32/32. L2: **run on hardware (2026-10-31 to 2026-11-06)**: every L2 extension has a GPU bundle (RTX 4060 Laptop GPU, WSL2) and a CPU-fallback bundle, all passing their invariants; the ch14 and Capstone H GPU bundles were rerun on 2026-11-06. Single-machine hands-on labs: 16 of 22 have passing reference runs. Per-lab hardware, software, date and result: [LAB_VALIDATION_MATRIX.md](LAB_VALIDATION_MATRIX.md). L3 (multi-node RDMA): **not run** | Lab engineer with GPU/RDMA access (L3) |
| G2 | Experienced GPU-cluster/network engineer reviews topology, RDMA, NCCL, checkpointing, failure-recovery chapters (5, 8, 9, 12, 13, 14, 19) | AI-assisted specialist reviews done 2026-11-05 ([reviews/](reviews/README.md)); **independent human review open** | External technical reviewer |
| G3 | Data-centre facilities specialist reviews power, liquid cooling, CDU, PDU, MEP material (2, 21) | AI-assisted review done 2026-11-05 ([reviews/facilities-economics-capstones.md](reviews/facilities-economics-capstones.md)); **independent human review open** | External facilities reviewer |
| G4 | Verify every `[VENDOR-SPEC]` claim and version-sensitive API against current primary documentation; record date and platform | **First pass done (2026-10-30):** 282 claims checked against primary sources (vendor docs, tagged source, standards): 244 OK, 12 WRONG fixed, 22 version qualifiers added, 4 unverifiable (already hedged). Per-group evidence in [verification/](verification/); shared facts in VERIFIED_FACTS.md. **Second pass done (2026-11-05):** Appendix E unverified claims resolved (Table E.13 verified, E.14 still unverified and hedged), versions checked, 0 of 102 links dead ([reviews/sources-versions.md](reviews/sources-versions.md)). Re-run before each printing — DCGM, NCCL, Kueue and vLLM changed names during 2026 | Technical editor |
| G5 | Run all benchmark and failure-injection procedures in a safe lab; preserve raw results | Partly done: L1 simulations, L2 bundles and 16 single-machine hands-on labs, raw results committed. Multi-node (L3) procedures and wave-B hands-on labs (ch07, 17, 18, 19, 20, 23) open | Lab engineer |
| G6 | Technical copyedit for terms, diagrams, units, acronyms, and measured-vs-illustrative separation | **Book-wide machine-assisted copyedit done (2026-10-30):** register in COPYEDIT_REGISTER.md (955 findings; ≈ 577 mechanical and ≈ 415 judgement edits applied, rest recorded as false positives). `scripts/copyedit_lint.py` → 0 findings in 113 files; 0 broken links or cross-references; units verified. Evidence in [verification/](verification/). **A human copyeditor's read-through is still recommended before print** | Copyeditor |
| G7 | Refresh job-market mapping (Chapter 24) with a dated, deduplicated register | **Done (2026-10-30):** 42 deduplicated roles from 11 employers' own listings (`lab/data/job_register_2026-10.csv`, report in [verification/G7-ch24.md](verification/G7-ch24.md)). Gaps: no hyperscalers, mostly US. Stale after 2026-11-29 — refresh before publication | Author |

## 3. External review of the concise PDF (2026-11-03)

An outside reader of the concise-edition PDF rated it **9.0/10** provisionally. That review is
separate from the internal 9.77 chapter-review average. It listed ten corrections. Here is where each
stands:

| # | Item | Status |
|---|---|---|
| 1 | Ch 6 statistical testing and Table 6.7 | **Done.** One primary statistic is used for the observed effect, the permutation test and the bootstrap CI, and every value is reproduced by running the published code. Tests were added. The permutation-test code was rewritten so the loop can't be misread when the line wraps. |
| 2 | Synchronize the concise edition | **Done.** It was re-synced with 702c844. The copyright page prints the commit and build date, and `build/concise/BUILD_MANIFEST.json` records the version, commit, date and SHA-256 of each output. |
| 3 | GPU hardware reruns (ch04, ch14, ch24 L2 bundles) | **Open (G1/G5).** These need the GPU host and Docker. The experiment guards are in place, and the bundles carry errata until rerun. |
| 4 | Independent GPU, network and facilities expert reviews | **Open (G2/G3).** No external review has taken place. Don't describe the book as independently validated. |
| 5 | ORION reference configuration | **Done.** See Appendix A of the concise edition. |
| 6 | Benchmark reporting standard | **Done.** See Appendix B. |
| 7 | Ch 15 inference reproducibility | **Done.** Ch 15 now has benchmark-configuration tables, theoretical vs. practical KV-cache concurrency, and a comparison of batching, paging, prefix caching and speculative decoding. |
| 8 | Ch 19 security threat model | **Done.** Ch 19 now has a threat-model table and a validation checklist. |
| 9 | Vendor references and versions | **Done for the concise edition.** Appendix E has 116 rows, 48 re-verified against tagged source on 2026-11-03. Re-run it before each printing. |
| 10 | Copyedit and navigation | **Partly done.** Reading paths, a readiness checklist (Appendix C) and a glossary (Appendix D, 271 entries) were added, and a cross-reference sweep was run. **A human professional copyedit is still open (G6).** |
