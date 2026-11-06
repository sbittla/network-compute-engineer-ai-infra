# Release readiness: final editorial blockers (2026-11-05)

Status of each item in the final pre-publication list. **Closed** means fixed and verified in this
repository. **Closed with caveat** means fixed, with a limitation stated in the book. **Open** means it
needs a person or a decision outside this repository. Evidence paths are relative to the repository root.

## A. Confirmed issues in the manuscript

| # | Item | Status | Evidence and resolution |
|---|---|---|---|
| 1 | Chapter 14 GPU asynchronous-checkpoint lab failed its timing invariants | **Closed** | Diagnosed: the 7.8 GiB WSL2 host paged (0.01 GB/s D2H, 2,247 s `dcp.load`). The experiment's memory guard and swap-out invariant now catch this. Rerun on 2026-11-06 with swap disabled for the run: all invariants pass (dcp.save 1.05 s; async_save blocks 0.57 s, 0.099 s with cached pinned staging; D2H 13.1 GB/s of a 15.8 GB/s PCIe ceiling; restore bit-exact). `book/part-4-distributed-ai/ch14-*/lab/l2/results/gpu-rtx-4060-laptop-gpu/`. The chapter, lab README and review record now present it as a valid run on a laptop GPU, not as ORION evidence. Capstone H's GPU bundle, which had ended in `error`, was rerun the same way and passes. |
| 2 | Typesetting defect "latest.The L2 extension" | **Closed** | Fixed in `concise/ch14.md`. A full text-extraction pass over the PDF for a missing space after a full stop found no other instance; `scripts/copyedit_lint.py` reports 0 findings. |
| 3 | Independent technical review not established | **Open (external)** | Seven AI-assisted specialist reviews (GPU systems, networking/RDMA, distributed training and storage, inference, operations and security, facilities and economics, sources) were completed, with every finding and resolution recorded in `docs/reviews/`. They are **not** independent human reviews, and the front matter now says so. Independent reviewers are still needed for gates G2 and G3 (`docs/RELEASE_GATES.md`). |
| 4 | Hardware validation not established for every lab | **Closed with caveat** | `docs/LAB_VALIDATION_MATRIX.md` (generated from committed evidence by `scripts/make_validation_matrix.py`): every L1 lab and capstone passes its test suite (2,160 tests); every L2 extension has a passing GPU bundle (RTX 4060 Laptop GPU, WSL2) and CPU-fallback bundle; 16 single-machine hands-on labs pass. Caveats stated in the matrix and front matter: L2 ran on a laptop GPU, not an H100-class host; L3 multi-node extensions have not been run; 6 hands-on labs (ch07, 17, 18, 19, 20, 23) are not built (they need Docker). |

## B. Technical and content gates

| # | Item | Status | Evidence and resolution |
|---|---|---|---|
| 5 | ORION could be mistaken for a real deployment | **Closed** | ORION is called illustrative or fictional at first use in Chapter 1 and its Figure 1.1, in Chapter 11 (first use in Part 4), on the copyright page, in Appendix A, in every capstone brief (new "Fictional setting" note), and on the KDP description and back cover. ORION figures and tables in Chapters 7–10 carry `[ILLUSTRATIVE]`. |
| 6 | Evidence-label consistency | **Closed** | Audited chapter by chapter. Fixes include a `[MEASURED]` KV figure that was modeled (ch15), a non-standard label (ch14), a fictional policy labelled VENDOR-SPEC (ch18), a bare `[MEASURED]` now naming its host (ch04), and a synthetic figure now `[SIMULATED]` (ch09). |
| 7 | Unverified vendor claims (Appendix E.13) | **Closed with caveat** | Claims verified against primary sources moved to the new verified Table E.13 (13 rows). Three remain unverified in Table E.14 and are hedged in the chapter text. |
| 8 | Version-sensitive guidance | **Closed** | Every version in Appendix E exists and is framed "as of X". One chapter error corrected (Nsight Compute's clock lock changed from base to boost in 2026.1). `docs/REFERENCE_CLUSTER.md` software baseline aligned with Appendix E. 0 of 102 source links dead. |
| 9 | H100/HGX-specific guidance presented as general | **Closed** | Scoping qualifiers added where values are H100 SXM / HGX H100 specific (ch01, ch03, ch05, ch10, ch15 and others; see each review log). |
| 10 | Distributed-training recovery completeness | **Closed** | Review verdict: pass after adding elastic relaunch (`torchrun --max-restarts`, `--nnodes=MIN:MAX`, re-shardable checkpoints) to Chapter 11. Chapter 19's recovery coverage is consistent with Chapter 14. |
| 11 | Inference-serving completeness | **Closed** | Review verdict: sufficient for an infrastructure book. Added serving economics (cost per million tokens), autoscaling-versus-burst guidance and corrected V1 preemption and metric names; pipeline parallelism added to the full edition. |
| 12 | Security and multi-tenancy completeness | **Closed** | Review verdict: pass. Added measured boot and TPM attestation, and IPMI reachability, to the security controls; MPS is no longer called acceptable for multi-tenant production; security sources added to Appendix E. |
| 13 | Operational safety of lab instructions | **Closed** | Chapters 16–20 lab READMEs gained cleanup and restore steps (taints, quotas, drains, rail and link tests), an MTU lock-out warning, and secrets moved off the command line. Network labs run in throwaway namespaces. Every lab and hands-on README has a Troubleshooting section. |
| 14 | Recompute worked examples | **Closed** | Every reviewer recomputed its chapters' models (memory, bandwidth, roofline, collectives, PFC headroom, checkpoint sizing, recovery, power, cooling, TCO). The models reproduced except where a log records a fix: ch09 PFC headroom resized for 50 m host cables (93,496 B/port), ch02 goodput aligned to 0.88, ch02 rack-unit count, ch21 glycol flow, ch22 small-sample MDE. |
| 15 | Limitations of simulated results | **Closed** | Simulated results in Chapters 12–15 and 21 now state what they omit; TCO prices are stated as teaching assumptions, not purchasing quotes. |

## C. Editorial, instructional and publishing gates

| # | Item | Status | Evidence and resolution |
|---|---|---|---|
| 16 | Concise-edition scope clarity | **Closed** | New "What is in this book, and what is in the companion repository" paragraph in About This Edition, plus the "Using the Practice Material" front-matter page. |
| 17 | Book-to-repository consistency | **Closed** | Every repository path printed in the book (182 checked) resolves in the repository. The unresolved ones are upstream source files cited in Appendix E, IP-address patterns or generic names, none of them repository paths. |
| 18 | Lab dependencies | **Closed** | Per-lab hardware, software and limitations in `docs/LAB_VALIDATION_MATRIX.md`; every L2 extension has a CPU fallback (committed `cpu-fallback` bundles); no lab needs a cloud account or credentials. Network access is needed only to install the pinned Python packages and, for hands-on labs, what each `setup.sh` installs; the Chapter 15 hands-on `setup.sh` also downloads the public Qwen2.5-1.5B-Instruct model (3.1 GB, no Hugging Face account needed), after which runs are offline. |
| 19 | Exercise and answer-key alignment for this edition | **Closed** | The print edition cites no exercise ID that does not exist; every chapter's printed exercise count matches its folders; the package suite checks every prompt against `exercises.md` and regenerates every reference output (`docs/TEST_RESULTS.md`). |
| 20 | Capstone reproducibility | **Closed** | All eight briefs have quick starts, prerequisites, deliverables, the rubric and reproducible evidence requirements; each starter checker's actual count matches the brief; harness passes for all eight. |
| 21 | Source and bibliography quality | **Closed** | Titles, authors, venues and RFC numbers verified; two RFC metadata fixes; 0 of 102 links dead (`docs/reviews/sources-versions.md`). |
| 22 | Figure and diagram accuracy | **Closed** | Every Mermaid diagram checked against its prose; one fixed (Fig. 14.2 completion arrow). |
| 23 | Print and ebook rendering | **Closed** | 405-page 7 × 10 in PDF: no missing glyphs, all special symbols present, 35 diagrams, 136 external and 258 internal links, no blank pages, nothing within 0.25 in of the trim edge, body text 10.5 pt. **All fonts are now embedded** (the page numbers had used a non-embedded Helvetica, which KDP rejects). The DOCX (ebook source) has the same 35 images and content. |
| 24 | Author biography and credentials | **Open (author)** | The biography's employers, patents, awards and book list can only be confirmed by the author. Please check `concise/about-the-author.md` and the back-cover bio in `cover/make_covers.py`. |
| 25 | Publication rights and permissions | **Closed** | All figures are original diagrams generated from the book's own Mermaid source; no screenshots or third-party images; the copyright page carries a trademark notice. The repository now has a `LICENSE`: MIT for code, scripts and lab data; book text, figures and covers all rights reserved. The copyright page states it. |
| 26 | Release identity and metadata | **Closed** | Title, subtitle, First Edition, author and both ISBNs (paperback 9798167679542, hardcover 9798167679764) agree across the build script, copyright page, covers and KDP description. PDF metadata now carries title, author, subject and ISBNs. The final print files must be built from a clean commit, so the copyright page does not say "with uncommitted changes". |

## Covers

The interior grew to 405 pages, so the covers were regenerated for 406 (even) pages: paperback spine
0.914 in, hardcover spine 1.103 in (`build/cover/`). Stale 396- and 400-page cover files were removed.

## Chapter 24 job register

Refreshed on 2026-11-06 (67 postings read, 60 recorded, 50 roles at 11 employers; 47 of the 2026-10-30
snapshot's 50 requisitions still open). Both editions, the lab check, exercise R4's solver and the answer key
use the new files; the 2026-10 snapshot is kept for comparison. The register is stale after **2026-12-06**:
if publication slips past that date, refresh it again with the method in `register_meta_2026-11.yaml`.
